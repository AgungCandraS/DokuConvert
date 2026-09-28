"""Maps stable operation keys to converter adapters."""

from __future__ import annotations

from app.backend.converters.base import ConverterAdapter
from app.backend.converters.image_to_pdf import ImageToPdfConverter
from app.backend.converters.office_to_pdf import OfficeToPdfConverter
from app.backend.converters.pdf_operations import PdfOperationsConverter
from app.backend.converters.pdf_to_docx import PdfToDocxConverter
from app.backend.converters.pdf_to_image import PdfToImageConverter
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import EnvironmentCheck
from app.backend.infrastructure.libreoffice_runner import LibreOfficeRunner


class ConverterRegistry:
    def __init__(
        self,
        adapters: list[ConverterAdapter] | None = None,
        *,
        libreoffice_timeout_seconds: int = 300,
        libreoffice_executable: str | None = None,
    ) -> None:
        runner = LibreOfficeRunner(
            timeout_seconds=libreoffice_timeout_seconds,
            preferred_path=libreoffice_executable,
        )
        self.libreoffice_runner = runner
        selected = adapters if adapters is not None else [
            OfficeToPdfConverter(runner),
            PdfToDocxConverter(),
            ImageToPdfConverter(),
            PdfToImageConverter(),
            PdfOperationsConverter(),
        ]
        self._by_operation: dict[OperationType, ConverterAdapter] = {}
        for adapter in selected:
            for operation in adapter.operations:
                if operation in self._by_operation:
                    raise ValueError(f"Duplicate converter registered for {operation}")
                self._by_operation[operation] = adapter

    def set_libreoffice_executable(self, executable: str | None) -> None:
        """Update Office conversions after the user changes the executable in settings."""
        self.libreoffice_runner.executable = executable

    def get(self, operation: OperationType) -> ConverterAdapter:
        try:
            return self._by_operation[operation]
        except KeyError as exc:
            raise BackendError("unsupported_operation", "Jenis operasi dokumen belum tersedia.") from exc

    def environment_checks(self) -> list[EnvironmentCheck]:
        checks: list[EnvironmentCheck] = []
        seen: set[int] = set()
        for adapter in self._by_operation.values():
            if id(adapter) not in seen:
                seen.add(id(adapter))
                checks.extend(adapter.validate_environment())
        return checks
