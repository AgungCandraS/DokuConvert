"""Cooperative cancellation and progress reporting for converter adapters."""

from __future__ import annotations

from collections.abc import Callable

from app.backend.domain.errors import JobCancelled


class ProgressReporter:
    def __init__(
        self,
        cancel_check: Callable[[], bool],
        on_progress: Callable[[int, str], None],
        on_warning: Callable[[str], None],
    ) -> None:
        self._cancel_check = cancel_check
        self._on_progress = on_progress
        self._on_warning = on_warning

    def check_cancelled(self) -> None:
        if self._cancel_check():
            raise JobCancelled

    @property
    def cancelled(self) -> bool:
        return self._cancel_check()

    def update(self, current: int, total: int, message: str = "Memproses file") -> None:
        self.check_cancelled()
        value = max(0, min(100, int(current * 100 / max(total, 1))))
        self._on_progress(value, message)

    def warning(self, message: str) -> None:
        self._on_warning(message)
