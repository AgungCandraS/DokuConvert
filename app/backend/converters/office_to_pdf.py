"""Office and OpenDocument conversion using one isolated LibreOffice profile per file."""

from __future__ import annotations

from pathlib import Path

from app.backend.application.progress import ProgressReporter
from app.backend.converters.base import ConverterAdapter
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError, JobCancelled
from app.backend.domain.models import ConversionJob, EnvironmentCheck
from app.backend.infrastructure.filesystem import safe_stem
from app.backend.infrastructure.libreoffice_runner import LibreOfficeRunner

_OFFICE_OPERATIONS = {
    OperationType.WORD_TO_PDF,
    OperationType.EXCEL_TO_PDF,
    OperationType.POWERPOINT_TO_PDF,
    OperationType.ODT_TO_PDF,
}


class OfficeToPdfConverter(ConverterAdapter):
    operations = frozenset(_OFFICE_OPERATIONS)

    def __init__(self, runner: LibreOfficeRunner) -> None:
        self.runner = runner

    def validate_environment(self) -> list[EnvironmentCheck]:
        return [self.runner.validate_environment()]

    def convert(self, job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        outputs: list[Path] = []
        stem_counts: dict[str, int] = {}
        for source in job.source_files:
            stem = safe_stem(source.stem).casefold()
            stem_counts[stem] = stem_counts.get(stem, 0) + 1
        for index, source in enumerate(job.source_files, start=1):
            reporter.check_cancelled()
            reporter.update(index - 1, len(job.source_files), f"Mengonversi {source.name}")
            per_file = workspace / f"office-{index}"
            per_file.mkdir()
            try:
                raw_output = self.runner.convert_to_pdf(source, per_file, reporter)
                output_stem = safe_stem(source.stem)
                if stem_counts[output_stem.casefold()] > 1:
                    output_stem = f"{output_stem}_{index}"
                output = workspace / f"{output_stem}_converted.pdf"
                raw_output.replace(output)
                outputs.append(output)
            except JobCancelled:
                raise
            except BackendError as exc:
                if len(job.source_files) == 1:
                    raise
                reporter.warning(f"{source.name}: {exc.message}")
            reporter.update(index, len(job.source_files), f"Selesai memeriksa {source.name}")
        if not outputs:
            raise BackendError(
                "batch_conversion_failed",
                "Tidak ada file yang berhasil dikonversi.",
                "Periksa format dan kondisi setiap file sumber.",
            )
        return outputs
