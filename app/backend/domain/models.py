"""UI-independent data models used by validation, converters, and job workers."""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from app.backend.domain.enums import JobStatus, OperationType


@dataclass(slots=True)
class ConversionJob:
    operation: OperationType
    source_files: list[Path]
    output_directory: Path
    options: dict[str, Any] = field(default_factory=dict, repr=False)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: JobStatus = JobStatus.QUEUED
    progress: int = 0
    progress_message: str = "Menunggu antrean"
    output_files: list[Path] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    error_recovery: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now().astimezone())
    started_at: datetime | None = None
    finished_at: datetime | None = None
    _cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)

    def cancel(self) -> None:
        self._cancel_event.set()

    @property
    def cancellation_requested(self) -> bool:
        return self._cancel_event.is_set()


@dataclass(frozen=True, slots=True)
class ConversionResult:
    success: bool
    output_files: list[Path]
    warnings: list[str]
    duration_ms: int
    source_file_count: int


@dataclass(frozen=True, slots=True)
class EnvironmentCheck:
    name: str
    available: bool
    message: str
    executable: str | None = None


@dataclass(frozen=True, slots=True)
class JobEvent:
    job_id: str
    status: JobStatus
    progress: int
    message: str
    output_files: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
    error_code: str | None = None
    error_message: str | None = None
    error_recovery: str | None = None
