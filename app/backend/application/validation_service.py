"""Validate job shape, file access, supported formats, and readable content."""

from __future__ import annotations

import os
import uuid
import warnings
import zipfile
from pathlib import Path

from app.backend.config import BackendConfig
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob

OPERATION_EXTENSIONS: dict[OperationType, frozenset[str]] = {
    OperationType.WORD_TO_PDF: frozenset({".docx", ".odt"}),
    OperationType.EXCEL_TO_PDF: frozenset({".xlsx"}),
    OperationType.POWERPOINT_TO_PDF: frozenset({".pptx"}),
    OperationType.ODT_TO_PDF: frozenset({".odt"}),
    OperationType.PDF_TO_DOCX: frozenset({".pdf"}),
    OperationType.IMAGE_TO_PDF: frozenset({".jpg", ".jpeg", ".png"}),
    OperationType.PDF_TO_IMAGE: frozenset({".pdf"}),
    OperationType.MERGE_PDF: frozenset({".pdf"}),
    OperationType.SPLIT_PDF: frozenset({".pdf"}),
    OperationType.COMPRESS_PDF: frozenset({".pdf"}),
    OperationType.ROTATE_PDF: frozenset({".pdf"}),
    OperationType.DELETE_PAGES: frozenset({".pdf"}),
    OperationType.WATERMARK_PDF: frozenset({".pdf"}),
    OperationType.PROTECT_PDF: frozenset({".pdf"}),
}

_SINGLE_INPUT = {
    OperationType.PDF_TO_DOCX,
    OperationType.PDF_TO_IMAGE,
    OperationType.SPLIT_PDF,
    OperationType.COMPRESS_PDF,
    OperationType.ROTATE_PDF,
    OperationType.DELETE_PAGES,
    OperationType.WATERMARK_PDF,
    OperationType.PROTECT_PDF,
}


class ValidationService:
    def __init__(self, config: BackendConfig) -> None:
        self.config = config

    def validate(self, job: ConversionJob) -> list[Path]:
        if not isinstance(job.operation, OperationType):
            raise BackendError("unsupported_operation", "Jenis operasi dokumen tidak didukung.")
        try:
            parsed_id = uuid.UUID(job.id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise BackendError("invalid_job_id", "Identitas job tidak valid.") from exc
        if str(parsed_id) != job.id.lower():
            raise BackendError("invalid_job_id", "Identitas job tidak valid.")
        minimum = 2 if job.operation == OperationType.MERGE_PDF else 1
        if len(job.source_files) < minimum:
            message = "Pilih setidaknya dua file PDF untuk digabungkan." if minimum == 2 else "Pilih setidaknya satu file sumber."
            raise BackendError("not_enough_sources", message)
        if job.operation in _SINGLE_INPUT and len(job.source_files) != 1:
            raise BackendError("too_many_sources", "Operasi ini hanya menerima satu file sumber.")

        output_directory = Path(job.output_directory).expanduser()
        if not output_directory.exists() or not output_directory.is_dir():
            raise BackendError(
                "output_directory_missing",
                "Folder output tidak ditemukan.",
                "Pilih folder penyimpanan yang tersedia.",
            )
        if not os.access(output_directory, os.W_OK):
            raise BackendError("output_directory_read_only", "Folder output tidak dapat ditulisi.")

        canonical_paths: list[Path] = []
        seen: set[Path] = set()
        allowed = OPERATION_EXTENSIONS[job.operation]
        for raw_path in job.source_files:
            source = Path(raw_path).expanduser()
            try:
                source = source.resolve(strict=True)
            except OSError as exc:
                raise BackendError(
                    "source_missing",
                    f"File sumber tidak ditemukan: {Path(raw_path).name}",
                    "Periksa kembali lokasi file dan coba lagi.",
                    technical_detail=str(exc),
                ) from exc
            if not source.is_file() or not os.access(source, os.R_OK):
                raise BackendError(
                    "source_unreadable",
                    f"File tidak dapat dibaca: {source.name}",
                    "Tutup aplikasi lain yang sedang memakai file tersebut atau pilih salinannya.",
                )
            if source.suffix.lower() not in allowed:
                raise BackendError(
                    "unsupported_format",
                    f"Format {source.suffix or 'tanpa ekstensi'} tidak didukung untuk operasi ini.",
                    f"Gunakan file {', '.join(sorted(allowed))}.",
                )
            if source in seen:
                raise BackendError("duplicate_source", "File sumber yang sama dipilih lebih dari sekali.")
            seen.add(source)
            try:
                size = source.stat().st_size
            except OSError as exc:
                raise BackendError("source_unreadable", "Informasi file sumber tidak dapat dibaca.") from exc
            if size == 0:
                raise BackendError("empty_source", f"File {source.name} kosong.")
            if self.config.max_file_size_bytes and size > self.config.max_file_size_bytes:
                limit_mb = self.config.max_file_size_bytes / (1024 * 1024)
                raise BackendError(
                    "source_too_large",
                    f"File {source.name} melewati batas ukuran {limit_mb:g} MB.",
                    "Pilih file yang lebih kecil atau ubah batas ukuran di konfigurasi.",
                )
            self._validate_content(source, str(job.options.get("source_password", "")))
            canonical_paths.append(source)

        job.source_files = canonical_paths
        job.output_directory = output_directory.resolve()
        return canonical_paths

    @staticmethod
    def _validate_content(source: Path, password: str = "") -> None:
        if source.suffix.lower() == ".pdf":
            try:
                import pymupdf

                with pymupdf.open(source) as document:
                    if document.needs_pass:
                        if not password or not document.authenticate(password):
                            raise BackendError(
                                "password_required",
                                f"File {source.name} dilindungi password.",
                                "Masukkan password file yang benar lalu coba lagi.",
                            )
                    if document.page_count == 0:
                        raise BackendError("invalid_pdf", f"File {source.name} tidak berisi halaman PDF.")
            except BackendError:
                raise
            except ImportError as exc:
                raise BackendError(
                    "dependency_missing", "Komponen PDF belum terpasang.", "Pasang dependency backend PDF.",
                    technical_detail="PyMuPDF is not installed",
                ) from exc
            except Exception as exc:
                raise BackendError(
                    "invalid_pdf",
                    f"File {source.name} bukan PDF yang dapat dibaca.",
                    "Periksa file atau buat ulang PDF dari aplikasi sumber.",
                    technical_detail=str(exc),
                ) from exc
            return

        if source.suffix.lower() in {".jpg", ".jpeg", ".png"}:
            try:
                from PIL import Image

                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    image_context = Image.open(source)
                with image_context as image:
                    expected = "JPEG" if source.suffix.lower() in {".jpg", ".jpeg"} else "PNG"
                    if image.format != expected:
                        raise BackendError(
                            "format_mismatch",
                            f"Isi file {source.name} tidak sesuai dengan ekstensi namanya.",
                            "Pilih file JPG atau PNG yang benar.",
                        )
                    if image.width * image.height > 50_000_000:
                        raise BackendError(
                            "image_too_large",
                            f"Resolusi gambar {source.name} terlalu besar untuk diproses dengan aman.",
                            "Gunakan gambar dengan resolusi di bawah 50 megapiksel.",
                        )
                    image.verify()
            except BackendError:
                raise
            except ImportError as exc:
                raise BackendError(
                    "dependency_missing", "Komponen gambar belum terpasang.", "Pasang dependency backend gambar.",
                    technical_detail="Pillow is not installed",
                ) from exc
            except Exception as exc:
                raise BackendError(
                    "invalid_image",
                    f"File gambar {source.name} rusak atau tidak didukung.",
                    "Pilih gambar JPG atau PNG yang dapat dibuka.",
                    technical_detail=str(exc),
                ) from exc
            return

        required_members = {
            ".docx": "word/document.xml",
            ".xlsx": "xl/workbook.xml",
            ".pptx": "ppt/presentation.xml",
            ".odt": "content.xml",
        }
        if source.suffix.lower() in required_members:
            try:
                with zipfile.ZipFile(source) as archive:
                    if required_members[source.suffix.lower()] not in archive.namelist():
                        raise BackendError(
                            "invalid_office_file",
                            f"File {source.name} bukan dokumen yang dapat dibaca.",
                            "Pastikan file tidak rusak dan ekstensi sesuai dengan formatnya.",
                        )
                    corrupt_member = archive.testzip()
                    if corrupt_member is not None:
                        raise BackendError(
                            "corrupt_office_file",
                            f"Struktur file {source.name} rusak.",
                            "Buka file di aplikasi asal, lalu simpan salinan baru.",
                        )
            except BackendError:
                raise
            except (OSError, zipfile.BadZipFile) as exc:
                raise BackendError(
                    "invalid_office_file",
                    f"File {source.name} bukan dokumen yang dapat dibaca.",
                    "Pastikan file tidak rusak dan ekstensi sesuai dengan formatnya.",
                    technical_detail=str(exc),
                ) from exc
