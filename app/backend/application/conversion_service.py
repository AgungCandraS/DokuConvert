"""Orchestrates validation, adapter execution, staging, and safe output publishing."""

from __future__ import annotations

import time
from pathlib import Path

from app.backend.application.progress import ProgressReporter
from app.backend.application.validation_service import ValidationService
from app.backend.config import BackendConfig
from app.backend.converters.registry import ConverterRegistry
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob, ConversionResult, EnvironmentCheck
from app.backend.infrastructure.filesystem import (
    JobWorkspace,
    cleanup_stale_temp_directories,
    publish_outputs,
    safe_stem,
)


class ConversionService:
    """UI-independent entry point for validation and running a conversion."""

    def __init__(
        self,
        config: BackendConfig | None = None,
        registry: ConverterRegistry | None = None,
    ) -> None:
        self.config = config or BackendConfig()
        self.registry = registry or ConverterRegistry(
            libreoffice_timeout_seconds=self.config.libreoffice_timeout_seconds,
            libreoffice_executable=self.config.libreoffice_executable,
        )
        self.validator = ValidationService(self.config)

    def set_libreoffice_executable(self, executable: str | None) -> None:
        self.registry.set_libreoffice_executable(executable)

    def validate(self, job: ConversionJob) -> list[Path]:
        self._apply_defaults(job)
        self.registry.get(job.operation)
        return self.validator.validate(job)

    def check_environment(self) -> list[EnvironmentCheck]:
        return self.registry.environment_checks()

    def run(
        self,
        job: ConversionJob,
        reporter: ProgressReporter,
    ) -> ConversionResult:
        started = time.monotonic()
        self.validate(job)
        adapter = self.registry.get(job.operation)
        cleanup_stale_temp_directories(job.output_directory)
        with JobWorkspace(job.output_directory, job.id) as workspace:
            reporter.check_cancelled()
            staged_outputs = adapter.convert(job, reporter, workspace)
            reporter.check_cancelled()
            for output in staged_outputs:
                if output.parent.resolve() != workspace.resolve():
                    raise BackendError("invalid_converter_output", "Converter menghasilkan lokasi output yang tidak valid.")
            staged_outputs = self._apply_output_name(job, staged_outputs)
            output_files = publish_outputs(staged_outputs, job.output_directory)
            if reporter.cancelled:
                for output in output_files:
                    try:
                        output.unlink(missing_ok=True)
                    except OSError:
                        pass
                reporter.check_cancelled()
        duration_ms = max(0, int((time.monotonic() - started) * 1000))
        return ConversionResult(
            success=bool(output_files),
            output_files=output_files,
            warnings=list(job.warnings),
            duration_ms=duration_ms,
            source_file_count=len(job.source_files),
        )

    @staticmethod
    def _apply_defaults(job: ConversionJob) -> None:
        defaults: dict[OperationType, dict[str, object]] = {
            OperationType.SPLIT_PDF: {"mode": "extract", "page_ranges": "1-3"},
            OperationType.COMPRESS_PDF: {"quality": "balanced"},
            OperationType.ROTATE_PDF: {"page_ranges": "1", "degrees": 90},
            OperationType.DELETE_PAGES: {"page_ranges": "1"},
            OperationType.WATERMARK_PDF: {"position": "center", "opacity": "medium"},
            OperationType.PDF_TO_IMAGE: {"image_format": "png", "dpi": 150},
            OperationType.IMAGE_TO_PDF: {
                "page_size": "a4", "orientation": "auto", "fit_to_page": True
            },
        }
        for key, value in defaults.get(job.operation, {}).items():
            job.options.setdefault(key, value)

    @staticmethod
    def _apply_output_name(job: ConversionJob, outputs: list[Path]) -> list[Path]:
        """Apply the UI's requested output name inside the isolated workspace."""
        requested = str(job.options.get("output_name", "")).strip()
        if not requested or not outputs:
            return outputs
        if Path(requested).name != requested or requested in {".", ".."}:
            raise BackendError("invalid_output_name", "Nama file hasil tidak valid.")

        filenames: list[str] | None = None
        if job.operation == OperationType.PDF_TO_IMAGE:
            prefix = safe_stem(Path(requested).stem if Path(requested).suffix else requested)
            filenames = [
                f"{prefix}-{index:03d}{output.suffix.lower()}"
                for index, output in enumerate(outputs, start=1)
            ]
        elif job.operation == OperationType.SPLIT_PDF and job.options.get("mode") == "ranges":
            prefix = safe_stem(Path(requested).stem if Path(requested).suffix else requested)
            ranges = [
                part.strip().replace("-", "_")
                for part in str(job.options.get("page_ranges", "")).split(",")
                if part.strip()
            ]
            filenames = []
            used_names: set[str] = set()
            for index in range(len(outputs)):
                page_range = safe_stem(
                    ranges[index] if index < len(ranges) else str(index + 1)
                )
                filename = f"{prefix}_{page_range}.pdf"
                if filename.casefold() in used_names:
                    filename = f"{prefix}_{page_range}_{index + 1}.pdf"
                used_names.add(filename.casefold())
                filenames.append(filename)
        elif len(outputs) == 1:
            output = outputs[0]
            requested_path = Path(requested)
            stem = safe_stem(requested_path.stem if requested_path.suffix else requested_path.name)
            suffix = output.suffix.lower()
            if requested_path.suffix.lower() == suffix:
                suffix = requested_path.suffix.lower()
            filenames = [f"{stem}{suffix}"]
        if filenames is None:
            return outputs

        # Two phases avoid a custom name colliding with another staged default name.
        staged: list[Path] = []
        for index, output in enumerate(outputs):
            temporary = output.with_name(f".{job.id}-{index}.rename")
            output.replace(temporary)
            staged.append(temporary)
        renamed: list[Path] = []
        for output, filename in zip(staged, filenames, strict=True):
            target = output.with_name(filename)
            output.replace(target)
            renamed.append(target)
        return renamed
