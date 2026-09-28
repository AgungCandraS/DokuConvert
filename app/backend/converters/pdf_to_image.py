"""Render each PDF page as a separate PNG or JPEG file."""

from __future__ import annotations

from pathlib import Path

import pymupdf

from app.backend.application.progress import ProgressReporter
from app.backend.converters.base import (
    ConverterAdapter,
    open_pdf,
    option_int,
    parse_page_ranges,
    source_is_password_protected,
)
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob
from app.backend.infrastructure.filesystem import safe_stem


class PdfToImageConverter(ConverterAdapter):
    operations = frozenset({OperationType.PDF_TO_IMAGE})

    def convert(self, job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        source = job.source_files[0]
        image_format = str(job.options.get("image_format", "png")).lower()
        if image_format not in {"png", "jpg", "jpeg"}:
            raise BackendError("invalid_option", "Format gambar harus PNG atau JPG.")
        dpi = option_int(job, "dpi", 150, 72, 300)
        extension = "jpg" if image_format == "jpeg" else image_format
        outputs: list[Path] = []
        requested_pages = str(job.options.get("page_ranges", "")).strip()
        if source_is_password_protected(source):
            reporter.warning("File gambar hasil tidak dilindungi password PDF sumber.")
        with open_pdf(source, str(job.options.get("source_password", ""))) as document:
            total = document.page_count
            page_indexes = (
                [page_index for group in parse_page_ranges(requested_pages, total) for page_index in group]
                if requested_pages
                else list(range(total))
            )
            for index, page_index in enumerate(page_indexes, start=1):
                page = document[page_index]
                reporter.update(index - 1, len(page_indexes), f"Merender halaman {page_index + 1} dari {total}")
                pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csRGB, alpha=False)
                output = workspace / f"{safe_stem(source.stem)}_page_{index:03d}.{extension}"
                if extension == "jpg":
                    pixmap.save(output, jpg_quality=92)
                else:
                    pixmap.save(output)
                outputs.append(output)
                reporter.update(index, len(page_indexes), f"Selesai merender halaman {page_index + 1} dari {total}")
        return outputs
