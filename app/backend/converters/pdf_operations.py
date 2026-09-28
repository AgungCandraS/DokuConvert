"""PDF merge, extract/split, compression, page edits, watermark, and protection."""

from __future__ import annotations

import os
import secrets
from pathlib import Path

import pymupdf

from app.backend.application.progress import ProgressReporter
from app.backend.converters.base import (
    ConverterAdapter,
    open_pdf,
    option_int,
    parse_page_ranges,
    require_option,
    save_pdf,
)
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob
from app.backend.infrastructure.filesystem import safe_stem

_PDF_OPERATIONS = {
    OperationType.MERGE_PDF,
    OperationType.SPLIT_PDF,
    OperationType.COMPRESS_PDF,
    OperationType.ROTATE_PDF,
    OperationType.DELETE_PAGES,
    OperationType.WATERMARK_PDF,
    OperationType.PROTECT_PDF,
}


class PdfOperationsConverter(ConverterAdapter):
    operations = frozenset(_PDF_OPERATIONS)

    def convert(self, job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        if job.operation == OperationType.MERGE_PDF:
            return self._merge(job, reporter, workspace)
        if job.operation == OperationType.SPLIT_PDF:
            return self._split(job, reporter, workspace)
        if job.operation == OperationType.COMPRESS_PDF:
            return self._compress(job, reporter, workspace)
        if job.operation == OperationType.ROTATE_PDF:
            return self._rotate(job, reporter, workspace)
        if job.operation == OperationType.DELETE_PAGES:
            return self._delete_pages(job, reporter, workspace)
        if job.operation == OperationType.WATERMARK_PDF:
            return self._watermark(job, reporter, workspace)
        if job.operation == OperationType.PROTECT_PDF:
            return self._protect(job, reporter, workspace)
        raise BackendError("unsupported_operation", "Operasi PDF tidak didukung.")

    @staticmethod
    def _merge(job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        merged = pymupdf.open()
        try:
            for index, source in enumerate(job.source_files, start=1):
                reporter.update(index - 1, len(job.source_files), f"Menggabungkan {source.name}")
                with open_pdf(source, str(job.options.get("source_password", ""))) as document:
                    merged.insert_pdf(document)
                reporter.update(index, len(job.source_files), f"Menambahkan {source.name}")
            output = workspace / f"{safe_stem(job.source_files[0].stem)}_merged.pdf"
            save_pdf(merged, output, job, job.source_files, garbage=4, deflate=True)
        finally:
            merged.close()
        return [output]

    @staticmethod
    def _split(job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        source = job.source_files[0]
        mode = str(job.options.get("mode", "extract")).lower()
        if mode not in {"extract", "ranges"}:
            raise BackendError("invalid_option", "Mode pemisahan halaman tidak didukung.")
        with open_pdf(source, str(job.options.get("source_password", ""))) as document:
            groups = parse_page_ranges(str(job.options.get("page_ranges", "")), document.page_count)
            if mode == "extract":
                output = pymupdf.open()
                try:
                    for index, pages in enumerate(groups):
                        reporter.check_cancelled()
                        for page_index in pages:
                            output.insert_pdf(document, from_page=page_index, to_page=page_index)
                        reporter.update(index + 1, len(groups), "Mengambil halaman terpilih")
                    target = workspace / f"{safe_stem(source.stem)}_pages.pdf"
                    save_pdf(output, target, job, job.source_files, garbage=4, deflate=True)
                finally:
                    output.close()
                return [target]

            outputs: list[Path] = []
            for group_index, pages in enumerate(groups, start=1):
                reporter.check_cancelled()
                output = pymupdf.open()
                try:
                    for page_index in pages:
                        output.insert_pdf(document, from_page=page_index, to_page=page_index)
                    target = workspace / f"{safe_stem(source.stem)}_range_{group_index:03d}.pdf"
                    save_pdf(output, target, job, job.source_files, garbage=4, deflate=True)
                    outputs.append(target)
                finally:
                    output.close()
                reporter.update(group_index, len(groups), f"Menyimpan rentang {group_index}")
            return outputs

    @staticmethod
    def _compress(job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        source = job.source_files[0]
        preset = str(job.options.get("quality", "balanced")).lower()
        settings = {
            "small": (144, 96, 45),
            "balanced": (180, 150, 70),
            "quality": (240, 200, 85),
            "low": (144, 96, 45),
            "high": (240, 200, 85),
        }
        if preset not in settings:
            raise BackendError("invalid_option", "Preset kompresi PDF tidak didukung.")
        threshold, target, image_quality = settings[preset]
        output = workspace / f"{safe_stem(source.stem)}_compressed.pdf"
        with open_pdf(source, str(job.options.get("source_password", ""))) as document:
            reporter.update(15, 100, "Mengoptimalkan gambar dan struktur PDF")
            document.rewrite_images(
                dpi_threshold=threshold,
                dpi_target=target,
                quality=image_quality,
            )
            reporter.check_cancelled()
            save_pdf(document, output, job, job.source_files, garbage=4, deflate=True, clean=True)
        if output.stat().st_size >= source.stat().st_size:
            reporter.warning(
                "Ukuran hasil optimasi tidak lebih kecil dari file sumber. File sumber tetap tersedia."
            )
        reporter.update(100, 100, "Selesai mengompres PDF")
        return [output]

    @staticmethod
    def _rotate(job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        source = job.source_files[0]
        degree = option_int(job, "degrees", 90, 90, 270)
        if degree not in {90, 180, 270}:
            raise BackendError("invalid_option", "Arah rotasi harus 90, 180, atau 270 derajat.")
        output = workspace / f"{safe_stem(source.stem)}_rotated.pdf"
        with open_pdf(source, str(job.options.get("source_password", ""))) as document:
            groups = parse_page_ranges(str(job.options.get("page_ranges", "")), document.page_count)
            pages = {page_index for group in groups for page_index in group}
            for index, page_index in enumerate(sorted(pages), start=1):
                reporter.check_cancelled()
                page = document[page_index]
                page.set_rotation((page.rotation + degree) % 360)
                reporter.update(index, len(pages), f"Memutar halaman {page_index + 1}")
            save_pdf(document, output, job, job.source_files, garbage=4, deflate=True)
        return [output]

    @staticmethod
    def _delete_pages(job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        source = job.source_files[0]
        output = workspace / f"{safe_stem(source.stem)}_edited.pdf"
        with open_pdf(source, str(job.options.get("source_password", ""))) as document:
            groups = parse_page_ranges(str(job.options.get("page_ranges", "")), document.page_count)
            pages = sorted({page_index for group in groups for page_index in group}, reverse=True)
            if len(pages) >= document.page_count:
                raise BackendError(
                    "cannot_delete_all_pages",
                    "Semua halaman tidak dapat dihapus dari PDF.",
                    "Sisakan setidaknya satu halaman pada file hasil.",
                )
            for index, page_index in enumerate(pages, start=1):
                reporter.check_cancelled()
                document.delete_page(page_index)
                reporter.update(index, len(pages), f"Menghapus halaman {page_index + 1}")
            save_pdf(document, output, job, job.source_files, garbage=4, deflate=True)
        return [output]

    @staticmethod
    def _watermark(job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        source = job.source_files[0]
        text = require_option(job, "text", label="Teks watermark")
        if len(text) > 200:
            raise BackendError("watermark_too_long", "Teks watermark terlalu panjang.", "Gunakan maksimal 200 karakter.")
        position = str(job.options.get("position", "center")).lower()
        if position not in {"center", "diagonal", "bottom"}:
            raise BackendError("invalid_option", "Posisi watermark tidak didukung.")
        opacity_name = str(job.options.get("opacity", "medium")).lower()
        opacity = {"low": 0.16, "thin": 0.16, "medium": 0.3, "high": 0.48, "clear": 0.48}.get(opacity_name)
        if opacity is None:
            raise BackendError("invalid_option", "Tingkat transparansi watermark tidak didukung.")
        output = workspace / f"{safe_stem(source.stem)}_watermark.pdf"
        font_file = _watermark_font()
        with open_pdf(source, str(job.options.get("source_password", ""))) as document:
            for index, page in enumerate(document, start=1):
                reporter.check_cancelled()
                width, height = page.rect.width, page.rect.height
                fontsize = min(40.0, max(16.0, width / max(len(text), 12) * 1.15))
                if position == "bottom":
                    point = pymupdf.Point(28, height - 32)
                    rotation = 0
                elif position == "diagonal":
                    point = pymupdf.Point(width * 0.17, height * 0.62)
                    rotation = 45
                else:
                    point = pymupdf.Point(width * 0.2, height * 0.52)
                    rotation = 0
                page.insert_text(
                    point,
                    text,
                    fontsize=fontsize,
                    fontname="watermarkfont" if font_file else "helv",
                    fontfile=str(font_file) if font_file else None,
                    color=(0.45, 0.45, 0.45),
                    morph=(point, pymupdf.Matrix(rotation)) if rotation else None,
                    fill_opacity=opacity,
                    overlay=True,
                )
                reporter.update(index, document.page_count, f"Menambahkan watermark halaman {index}")
            save_pdf(document, output, job, job.source_files, garbage=4, deflate=True)
        return [output]

    @staticmethod
    def _protect(job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        source = job.source_files[0]
        password = require_option(job, "password", label="Password PDF")
        if len(password) < 6:
            raise BackendError("password_too_short", "Password PDF harus memiliki minimal 6 karakter.")
        output = workspace / f"{safe_stem(source.stem)}_protected.pdf"
        with open_pdf(source, str(job.options.get("source_password", ""))) as document:
            reporter.update(30, 100, "Mengunci salinan PDF dengan password")
            owner_password = str(job.options.get("owner_password", "")) or secrets.token_urlsafe(24)
            document.save(
                output,
                garbage=4,
                deflate=True,
                encryption=pymupdf.PDF_ENCRYPT_AES_256,
                owner_pw=owner_password,
                user_pw=password,
            )
        reporter.update(100, 100, "Selesai melindungi PDF")
        return [output]


def _watermark_font() -> Path | None:
    candidates = []
    if os.name == "nt":
        windows = Path(os.environ.get("WINDIR", r"C:\Windows"))
        candidates.extend([windows / "Fonts" / "segoeui.ttf", windows / "Fonts" / "arial.ttf"])
    candidates.extend(
        [
            Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
            Path("/Library/Fonts/Arial Unicode.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        ]
    )
    return next((candidate for candidate in candidates if candidate.is_file()), None)
