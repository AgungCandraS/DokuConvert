"""Best-effort PDF-to-DOCX adapter for text-based PDFs."""

from __future__ import annotations

from pathlib import Path

from app.backend.application.progress import ProgressReporter
from app.backend.converters.base import ConverterAdapter, open_pdf, source_is_password_protected
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob, EnvironmentCheck
from app.backend.infrastructure.filesystem import safe_stem


class PdfToDocxConverter(ConverterAdapter):
    operations = frozenset({OperationType.PDF_TO_DOCX})

    def validate_environment(self) -> list[EnvironmentCheck]:
        try:
            from pdf2docx import Converter as _Converter

            return [EnvironmentCheck("pdf2docx", True, "Konversi PDF ke Word siap digunakan.")]
        except ImportError:
            return [EnvironmentCheck("pdf2docx", False, "Komponen PDF ke Word belum terpasang.")]

    def convert(self, job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        source = job.source_files[0]
        password = str(job.options.get("source_password", ""))
        if source_is_password_protected(source):
            reporter.warning("File Word hasil tidak dilindungi password PDF sumber.")
        with open_pdf(source, password) as document:
            has_text = any(page.get_text().strip() for page in document)
            page_count = document.page_count
        if not has_text:
            reporter.warning(
                "PDF tampaknya berisi hasil pindai tanpa teks. OCR belum tersedia, sehingga dokumen Word mungkin kosong."
            )
        reporter.update(5, 100, "Menyiapkan konversi PDF ke Word")
        try:
            from pdf2docx import Converter
        except ImportError as exc:
            raise BackendError(
                "pdf2docx_missing",
                "Komponen PDF ke Word belum terpasang.",
                "Pasang dependency pdf2docx lalu mulai ulang aplikasi.",
                technical_detail=str(exc),
            ) from exc

        output = workspace / f"{safe_stem(source.stem)}_converted.docx"
        converter = None
        try:
            converter = Converter(str(source), password=password or None)
            # Processing is native to pdf2docx; cancellation is checked before
            # and after the call because that API does not expose progress hooks.
            reporter.check_cancelled()
            converter.convert(str(output))
            reporter.update(100, 100, f"Selesai mengonversi {page_count} halaman")
            reporter.check_cancelled()
        except BackendError:
            raise
        except Exception as exc:
            raise BackendError(
                "pdf_to_docx_failed",
                f"PDF {source.name} tidak dapat diubah menjadi Word.",
                "PDF dengan tabel atau tata letak kompleks mungkin tidak dapat dikonversi dengan baik.",
                technical_detail=str(exc),
            ) from exc
        finally:
            if converter is not None:
                converter.close()
        return [output]
