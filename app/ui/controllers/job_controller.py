"""Bridge job requests and worker events between Qt views and the backend."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QObject, Signal, Slot

from app.backend.bootstrap import BackendRuntime
from app.backend.domain.enums import JobStatus, OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob, JobEvent
from app.ui.tool_catalog import TOOL_BY_KEY


class _JobEventRelay(QObject):
    """Marshal backend callbacks onto the controller's Qt thread."""

    received = Signal(object)


class JobController(QObject):
    """Translate the UI request contract into backend jobs and view events."""

    job_updated = Signal(object)
    history_changed = Signal()
    submission_failed = Signal(str, str)

    _TERMINAL = {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}

    def __init__(self, runtime: BackendRuntime, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.runtime = runtime
        self._relay = _JobEventRelay(self)
        self._relay.received.connect(self._on_job_event)
        self._unsubscribe = runtime.jobs.subscribe(self._relay.received.emit)

    def submit(self, request: object) -> str | None:
        if not isinstance(request, dict):
            self.submission_failed.emit(
                "Permintaan proses tidak valid.", "Kembali ke pengaturan alat lalu coba lagi."
            )
            return None
        try:
            tool_key = str(request["tool_key"])
            operation = OperationType(tool_key)
            options = self._backend_options(request.get("options", {}))
            output_name = str(request.get("output_name", "")).strip()
            if output_name:
                options["output_name"] = output_name
            job = ConversionJob(
                operation=operation,
                source_files=[Path(str(path)) for path in request.get("sources", [])],
                output_directory=Path(str(request["output_directory"])),
                options=options,
            )
            self.runtime.jobs.submit(job)
            return job.id
        except (BackendError, KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, BackendError):
                message = exc.message
                recovery = exc.recovery or "Periksa kembali file dan pengaturan, lalu coba lagi."
            else:
                message = "Permintaan proses tidak valid."
                recovery = "Pilih alat yang tersedia dan coba lagi."
            self.submission_failed.emit(message, recovery)
            return None

    def cancel(self, job_id: str) -> bool:
        return self.runtime.jobs.cancel(job_id)

    def history_entries(self, limit: int = 100) -> list[dict[str, object]]:
        entries = self.runtime.history.entries(limit)
        for entry in entries:
            operation = str(entry.get("operation", ""))
            tool = TOOL_BY_KEY.get(operation)
            entry["tool_key"] = operation
            entry["tool_name"] = tool.name if tool else operation.replace("_", " ").title()
            entry["message"] = str(entry.get("error_code") or "")
        return entries

    def clear_history(self) -> None:
        self.runtime.history.clear()
        self.history_changed.emit()

    def import_legacy_history(self, entries: object) -> int:
        """Move older QSettings history metadata into the backend store once."""
        if not isinstance(entries, list):
            return 0
        imported = 0
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            try:
                operation = OperationType(str(entry.get("tool_key", "")))
                status = JobStatus(str(entry.get("status", "")))
                raw_sources = entry.get("sources", [])
                raw_outputs = entry.get("outputs", [])
                if not isinstance(raw_sources, list) or not isinstance(raw_outputs, list):
                    continue
                sources = [Path(str(path)) for path in raw_sources]
                created_at = datetime.fromisoformat(str(entry["created_at"]))
                job = ConversionJob(
                    operation=operation,
                    source_files=sources,
                    output_directory=sources[0].parent if sources else Path.cwd(),
                )
                job.id = str(entry.get("job_id") or job.id)
                job.status = status
                job.created_at = created_at
                job.output_files = [Path(str(path)) for path in raw_outputs]
                self.runtime.history.add(
                    job, duration_ms=int(entry.get("duration_ms", 0) or 0)
                )
                imported += 1
            except (KeyError, TypeError, ValueError):
                continue
        return imported

    @Slot(object)
    def _on_job_event(self, event: object) -> None:
        if not isinstance(event, JobEvent):
            return
        self.job_updated.emit(event)
        if event.status in self._TERMINAL:
            self.history_changed.emit()

    @staticmethod
    def _backend_options(raw_options: object) -> dict[str, object]:
        if not isinstance(raw_options, dict):
            raise BackendError("invalid_options", "Pengaturan proses tidak valid.")
        options = dict(raw_options)
        if "split_mode" in options:
            options["mode"] = options.pop("split_mode")
        if "resolution" in options:
            options["dpi"] = options.pop("resolution")
        if "image_page_range" in options:
            options["page_ranges"] = options.pop("image_page_range")
        if "rotation" in options:
            options["degrees"] = options.pop("rotation")
        if "watermark_text" in options:
            options["text"] = options.pop("watermark_text")
        if "watermark_position" in options:
            options["position"] = options.pop("watermark_position")
        if "watermark_opacity" in options:
            opacity = options.pop("watermark_opacity")
            options["opacity"] = {"light": "low", "strong": "high"}.get(opacity, opacity)
        if options.get("page_size") == "image":
            options["page_size"] = "original"
        options.pop("password_confirm", None)
        return options

    def close(self) -> None:
        self._unsubscribe()
