"""Local document-processing backend, kept independent from the desktop UI."""

from app.backend.application.conversion_service import ConversionService
from app.backend.application.job_manager import JobManager
from app.backend.bootstrap import BackendRuntime, create_backend
from app.backend.domain.enums import JobStatus, OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob, ConversionResult, EnvironmentCheck, JobEvent

__all__ = [
    "ConversionJob",
    "ConversionResult",
    "BackendError",
    "BackendRuntime",
    "ConversionService",
    "EnvironmentCheck",
    "JobManager",
    "JobEvent",
    "JobStatus",
    "OperationType",
    "create_backend",
]
