"""Backend paths and conservative resource limits."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def user_data_directory() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return root / "DocuConvert"


@dataclass(frozen=True, slots=True)
class BackendConfig:
    data_directory: Path = user_data_directory()
    max_concurrent_jobs: int = 2
    max_file_size_bytes: int | None = None
    history_limit: int = 100
    libreoffice_timeout_seconds: int = 300
    libreoffice_executable: str | None = None

    @property
    def log_directory(self) -> Path:
        return self.data_directory / "logs"

    @property
    def history_database(self) -> Path:
        return self.data_directory / "history.sqlite3"

    @property
    def settings_file(self) -> Path:
        return self.data_directory / "settings.json"
