"""Normalize image orientation and create a consistently sized PDF."""

from __future__ import annotations

import io
from pathlib import Path

import pymupdf
from PIL import Image, ImageOps

from app.backend.application.progress import ProgressReporter
from app.backend.converters.base import ConverterAdapter
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob
from app.backend.infrastructure.filesystem import safe_stem

_PAGE_SIZES = {
    "a4": (595.28, 841.89),
    "letter": (612.0, 792.0),
}


class ImageToPdfConverter(ConverterAdapter):
    operations = frozenset({OperationType.IMAGE_TO_PDF})

    def convert(self, job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        size_name = str(job.options.get("page_size", "a4")).lower()
        if size_name not in {"a4", "letter", "original"}:
            raise BackendError("invalid_option", "Ukuran halaman gambar tidak didukung.")
        orientation = str(job.options.get("orientation", "auto")).lower()
        if orientation not in {"auto", "portrait", "landscape"}:
            raise BackendError("invalid_option", "Orientasi halaman tidak didukung.")
        fit_to_page = bool(job.options.get("fit_to_page", True))

        pdf = pymupdf.open()
        try:
            for index, source in enumerate(job.source_files, start=1):
                reporter.update(index - 1, len(job.source_files), f"Menyiapkan {source.name}")
                try:
                    with Image.open(source) as opened:
                        image = ImageOps.exif_transpose(opened)
                        if image.mode in {"RGBA", "LA"} or "transparency" in image.info:
                            rgba = image.convert("RGBA")
                            background = Image.new("RGB", rgba.size, "white")
                            background.paste(rgba, mask=rgba.getchannel("A"))
                            image = background
                        else:
                            image = image.convert("RGB")
                        image_bytes = io.BytesIO()
                        image.save(image_bytes, format="PNG", optimize=True)
                        image_width, image_height = image.size
                except Exception as exc:
                    raise BackendError(
                        "invalid_image",
                        f"Gambar {source.name} tidak dapat diproses.",
                        "Pilih file JPG atau PNG yang dapat dibuka.",
                        technical_detail=str(exc),
                    ) from exc

                if size_name == "original":
                    page_width = image_width * 72 / 150
                    page_height = image_height * 72 / 150
                else:
                    page_width, page_height = _PAGE_SIZES[size_name]
                    if orientation == "landscape" or (
                        orientation == "auto" and image_width > image_height
                    ):
                        page_width, page_height = max(page_width, page_height), min(page_width, page_height)
                    elif orientation == "portrait":
                        page_width, page_height = min(page_width, page_height), max(page_width, page_height)
                if page_width > 14_400 or page_height > 14_400:
                    raise BackendError(
                        "image_page_too_large",
                        f"Resolusi {source.name} terlalu besar untuk dijadikan satu halaman PDF.",
                        "Gunakan ukuran halaman A4 atau Letter.",
                    )
                page = pdf.new_page(width=page_width, height=page_height)
                margin = 18.0
                bounds = pymupdf.Rect(margin, margin, page_width - margin, page_height - margin)
                scale = (
                    min(bounds.width / image_width, bounds.height / image_height)
                    if fit_to_page else 72 / 150
                )
                scaled_width, scaled_height = image_width * scale, image_height * scale
                image_rect = pymupdf.Rect(
                    bounds.x0 + (bounds.width - scaled_width) / 2,
                    bounds.y0 + (bounds.height - scaled_height) / 2,
                    bounds.x0 + (bounds.width + scaled_width) / 2,
                    bounds.y0 + (bounds.height + scaled_height) / 2,
                )
                page.insert_image(image_rect, stream=image_bytes.getvalue())
                reporter.update(index, len(job.source_files), f"Menambahkan {source.name}")
            output = workspace / f"{safe_stem(job.source_files[0].stem)}_converted.pdf"
            pdf.save(output, garbage=4, deflate=True)
        finally:
            pdf.close()
        return [output]
