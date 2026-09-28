"""Expected, user-actionable backend errors."""


class BackendError(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        recovery: str = "",
        *,
        technical_detail: str = "",
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.recovery = recovery
        self.technical_detail = technical_detail


class JobCancelled(Exception):
    """Raised cooperatively when a running conversion is cancelled."""
