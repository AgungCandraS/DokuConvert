"""Display states exposed by the tool page for future job-engine integration."""

from enum import StrEnum


class JobViewState(StrEnum):
    READY = "ready"
    VALIDATING = "validating"
    PROCESSING = "processing"
    UNAVAILABLE = "unavailable"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
