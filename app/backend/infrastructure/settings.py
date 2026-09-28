"""Small atomic JSON settings store for non-UI backend preferences."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

_ALLOWED_KEYS = {
    "theme",
    "language",
    "output_directory",
    "compression_preset",
    "history_limit",
    "open_output",
}


class SettingsStore:
    def __init__(self, settings_file: Path) -> None:
        self.settings_file = Path(settings_file)
        self._lock = threading.RLock()

    def load(self) -> dict[str, Any]:
        with self._lock:
            try:
                value = json.loads(self.settings_file.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                return {}
        if not isinstance(value, dict):
            return {}
        return {key: item for key, item in value.items() if key in _ALLOWED_KEYS}

    def update(self, values: dict[str, Any]) -> None:
        if any(key not in _ALLOWED_KEYS for key in values):
            raise ValueError("Unsupported setting key")
        with self._lock:
            current = self.load()
            current.update(values)
            self.settings_file.parent.mkdir(parents=True, exist_ok=True)
            fd, temporary_name = tempfile.mkstemp(
                prefix=f".{self.settings_file.name}-", suffix=".tmp", dir=self.settings_file.parent
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    json.dump(current, stream, ensure_ascii=False, indent=2)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary_name, self.settings_file)
            except Exception:
                Path(temporary_name).unlink(missing_ok=True)
                raise
