"""Bounded worker pool, job lifecycle, cancellation, and progress events."""

from __future__ import annotations

import logging
import threading
from concurrent.futures import CancelledError, Future, ThreadPoolExecutor
from datetime import datetime
from typing import Callable

from app.backend.application.conversion_service import ConversionService
from app.backend.application.progress import ProgressReporter
from app.backend.config import BackendConfig
from app.backend.domain.enums import JobStatus, OperationType
from app.backend.domain.errors import BackendError, JobCancelled
from app.backend.domain.models import ConversionJob, ConversionResult, JobEvent
from app.backend.infrastructure.history_service import HistoryService

logger = logging.getLogger("docuconvert.backend")


class JobManager:
    """Run local conversion jobs away from the caller's thread.

    Subscribe to events for queue/progress/completion notifications. The initial
    queued event is emitted by submit(); subsequent events come from a worker.
    Callbacks must be thread-safe and marshal updates to a GUI thread as needed.
    """

    def __init__(
        self,
        service: ConversionService | None = None,
        *,
        config: BackendConfig | None = None,
        history: HistoryService | None = None,
    ) -> None:
        self.config = config or (service.config if service else BackendConfig())
        self.service = service or ConversionService(self.config)
        self.history = history or HistoryService(
            self.config.history_database, limit=self.config.history_limit
        )
        self._executor = ThreadPoolExecutor(
            max_workers=max(1, self.config.max_concurrent_jobs),
            thread_name_prefix="docuconvert-job",
        )
        self._lock = threading.RLock()
        self._jobs: dict[str, ConversionJob] = {}
        self._futures: dict[str, Future[ConversionResult | None]] = {}
        self._listeners: list[Callable[[JobEvent], None]] = []
        self._closed = False

    def subscribe(self, callback: Callable[[JobEvent], None]) -> Callable[[], None]:
        with self._lock:
            self._listeners.append(callback)

        def unsubscribe() -> None:
            with self._lock:
                if callback in self._listeners:
                    self._listeners.remove(callback)

        return unsubscribe

    def submit(self, job: ConversionJob) -> ConversionJob:
        if not isinstance(job.operation, OperationType):
            raise BackendError("unsupported_operation", "Jenis operasi dokumen tidak didukung.")
        with self._lock:
            if self._closed:
                raise RuntimeError("JobManager has been shut down")
            if job.id in self._jobs:
                raise ValueError(f"Duplicate job id: {job.id}")
            job.status = JobStatus.QUEUED
            job.progress = 0
            job.progress_message = "Menunggu antrean"
            self._jobs[job.id] = job
            self._emit_locked(job)
            self._futures[job.id] = self._executor.submit(self._execute, job.id)
        return job

    def get(self, job_id: str) -> ConversionJob | None:
        with self._lock:
            return self._jobs.get(job_id)

    def jobs(self) -> list[ConversionJob]:
        with self._lock:
            return sorted(self._jobs.values(), key=lambda job: job.created_at, reverse=True)

    def wait(self, job_id: str, timeout: float | None = None) -> ConversionResult | None:
        with self._lock:
            future = self._futures.get(job_id)
        if future is None:
            raise KeyError(job_id)
        try:
            return future.result(timeout=timeout)
        except CancelledError:
            return None

    def cancel(self, job_id: str) -> bool:
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None or job.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
                return False
            job.cancel()
            future = self._futures.get(job_id)
            if future is not None and future.cancel():
                job.status = JobStatus.CANCELLED
                job.progress_message = "Proses dibatalkan"
                job.finished_at = datetime.now().astimezone()
                self._emit_locked(job)
                self._record(job, duration_ms=0)
            return True

    def shutdown(self, *, wait: bool = True, cancel_pending: bool = False) -> None:
        with self._lock:
            self._closed = True
            if cancel_pending:
                for job in self._jobs.values():
                    if job.status in {JobStatus.QUEUED, JobStatus.RUNNING}:
                        job.cancel()
                        future = self._futures.get(job.id)
                        if job.status == JobStatus.QUEUED and future is not None and future.cancel():
                            self._finish_cancelled(job)
        self._executor.shutdown(wait=wait, cancel_futures=cancel_pending)

    def _execute(self, job_id: str) -> ConversionResult | None:
        job = self.get(job_id)
        if job is None:
            return None
        with self._lock:
            if job.cancellation_requested:
                self._finish_cancelled(job)
                return None
            job.status = JobStatus.RUNNING
            job.started_at = datetime.now().astimezone()
            job.progress_message = "Memvalidasi file"
            self._emit_locked(job)

        reporter = ProgressReporter(
            cancel_check=lambda: job.cancellation_requested,
            on_progress=lambda value, message: self._progress(job, value, message),
            on_warning=lambda warning: self._warning(job, warning),
        )
        try:
            result = self.service.run(job, reporter)
        except JobCancelled:
            with self._lock:
                self._finish_cancelled(job)
            return None
        except BackendError as exc:
            with self._lock:
                job.status = JobStatus.FAILED
                job.error_code = exc.code
                job.error_message = exc.message
                job.error_recovery = exc.recovery or None
                job.progress_message = exc.message
                job.finished_at = datetime.now().astimezone()
                self._emit_locked(job)
                self._record(job, duration_ms=self._duration_ms(job))
            logger.warning("job_failed id=%s operation=%s code=%s", job.id, job.operation.value, exc.code)
            return None
        except Exception:
            with self._lock:
                job.status = JobStatus.FAILED
                job.error_code = "unexpected_error"
                job.error_message = "Terjadi kesalahan saat memproses dokumen. Coba lagi."
                job.progress_message = job.error_message
                job.finished_at = datetime.now().astimezone()
                self._emit_locked(job)
                self._record(job, duration_ms=self._duration_ms(job))
            # OS/library exception messages can contain private paths.
            logger.error("job_failed id=%s operation=%s code=unexpected_error", job.id, job.operation.value)
            return None

        with self._lock:
            if job.cancellation_requested:
                for output in result.output_files:
                    try:
                        output.unlink(missing_ok=True)
                    except OSError:
                        logger.warning("cancelled_output_cleanup_failed id=%s", job.id)
                self._finish_cancelled(job)
                return None
            job.status = JobStatus.COMPLETED
            job.progress = 100
            job.output_files = result.output_files
            job.warnings = result.warnings
            job.progress_message = "Selesai dengan catatan" if result.warnings else "Selesai"
            job.finished_at = datetime.now().astimezone()
            self._emit_locked(job)
            self._record(job, duration_ms=result.duration_ms)
        logger.info(
            "job_completed id=%s operation=%s source_count=%d output_count=%d duration_ms=%d",
            job.id,
            job.operation.value,
            len(job.source_files),
            len(result.output_files),
            result.duration_ms,
        )
        return result

    def _progress(self, job: ConversionJob, value: int, message: str) -> None:
        with self._lock:
            if job.status != JobStatus.RUNNING:
                return
            job.progress = max(0, min(100, value))
            job.progress_message = message
            self._emit_locked(job)

    def _warning(self, job: ConversionJob, message: str) -> None:
        with self._lock:
            job.warnings.append(message)
            self._emit_locked(job)

    def _finish_cancelled(self, job: ConversionJob) -> None:
        job.status = JobStatus.CANCELLED
        job.progress_message = "Proses dibatalkan"
        job.finished_at = datetime.now().astimezone()
        self._emit_locked(job)
        self._record(job, duration_ms=self._duration_ms(job))

    def _emit_locked(self, job: ConversionJob) -> None:
        event = JobEvent(
            job_id=job.id,
            status=job.status,
            progress=job.progress,
            message=job.progress_message,
            output_files=tuple(job.output_files),
            warnings=tuple(job.warnings),
            error_code=job.error_code,
            error_message=job.error_message,
            error_recovery=job.error_recovery,
        )
        listeners = tuple(self._listeners)
        for listener in listeners:
            try:
                listener(event)
            except Exception:
                logger.warning("job_event_listener_failed id=%s", job.id)

    def _record(self, job: ConversionJob, *, duration_ms: int) -> None:
        try:
            self.history.add(job, duration_ms=duration_ms)
        except Exception:
            logger.warning("history_write_failed id=%s", job.id)

    @staticmethod
    def _duration_ms(job: ConversionJob) -> int:
        if job.started_at is None or job.finished_at is None:
            return 0
        return max(0, int((job.finished_at - job.started_at).total_seconds() * 1000))
