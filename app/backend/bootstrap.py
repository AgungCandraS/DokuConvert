"""Construct the standalone backend runtime without importing or modifying the UI."""

from __future__ import annotations

from dataclasses import dataclass

from app.backend.application.conversion_service import ConversionService
from app.backend.application.job_manager import JobManager
from app.backend.config import BackendConfig
from app.backend.domain.models import EnvironmentCheck
from app.backend.infrastructure.history_service import HistoryService
from app.backend.infrastructure.logging_setup import configure_logging
from app.backend.infrastructure.settings import SettingsStore


@dataclass(slots=True)
class BackendRuntime:
    config: BackendConfig
    conversions: ConversionService
    jobs: JobManager
    history: HistoryService
    settings: SettingsStore
    environment_checks: list[EnvironmentCheck]

    def close(self, *, wait_for_jobs: bool = True, cancel_pending: bool = False) -> None:
        self.jobs.shutdown(wait=wait_for_jobs, cancel_pending=cancel_pending)


def create_backend(config: BackendConfig | None = None) -> BackendRuntime:
    config = config or BackendConfig()
    config.data_directory.mkdir(parents=True, exist_ok=True)
    configure_logging(config.log_directory)
    conversions = ConversionService(config)
    environment_checks = conversions.check_environment()
    history = HistoryService(config.history_database, limit=config.history_limit)
    jobs = JobManager(conversions, config=config, history=history)
    settings = SettingsStore(config.settings_file)
    return BackendRuntime(config, conversions, jobs, history, settings, environment_checks)
