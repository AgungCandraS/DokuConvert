"""Converter contract and shared PDF/page-range helpers."""

from __future__ import annotations

import secrets
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pymupdf

from app.backend.application.progress import ProgressReporter
from app.backend.domain.enums import OperationType
from app.backend.domain.errors import BackendError
from app.backend.domain.models import ConversionJob, EnvironmentCheck


class ConverterAdapter(ABC):
    operations: frozenset[OperationType] = frozenset()

    @abstractmethod
    def convert(self, job: ConversionJob, reporter: ProgressReporter, workspace: Path) -> list[Path]:
        """Write output files under workspace and return their paths."""

    def validate_environment(self) -> list[EnvironmentCheck]:
        return []


def open_pdf(source: Path, password: str = "") -> pymupdf.Document:
    try:
        document = pymupdf.open(source)
    except Exception as exc:
        raise BackendError(
            "invalid_pdf",
            f"File {source.name} bukan PDF yang dapat dibaca.",
            "Periksa file atau buat ulang PDF dari aplikasi sumber.",
            technical_detail=str(exc),
        ) from exc
    if document.needs_pass and (not password or not document.authenticate(password)):
        document.close()
        raise BackendError(
            "password_required",
            f"File {source.name} dilindungi password.",
            "Masukkan password file yang benar lalu coba lagi.",
        )
    return document


def source_is_password_protected(source: Path) -> bool:
    try:
        with pymupdf.open(source) as document:
            return document.needs_pass
    except Exception as exc:
        raise BackendError(
            "invalid_pdf",
            f"File {source.name} bukan PDF yang dapat dibaca.",
            "Periksa file atau buat ulang PDF dari aplikasi sumber.",
            technical_detail=str(exc),
        ) from exc


def save_pdf(
    document: pymupdf.Document,
    destination: Path,
    job: ConversionJob,
    source_files: list[Path],
    **options: Any,
) -> None:
    """Retain input PDF password protection when writing a modified PDF."""
    protected = any(source_is_password_protected(source) for source in source_files)
    if protected:
        password = str(job.options.get("source_password", ""))
        if not password:
            raise BackendError("password_required", "Masukkan password PDF sebelum menyimpan hasil.")
        options.update(
            encryption=pymupdf.PDF_ENCRYPT_AES_256,
            owner_pw=secrets.token_urlsafe(24),
            user_pw=password,
        )
    document.save(destination, **options)


def parse_page_ranges(value: str, page_count: int) -> list[list[int]]:
    """Parse user-facing 1-based ranges into ordered, zero-based page groups."""
    if not value.strip():
        raise BackendError("page_range_required", "Nomor halaman belum diisi.", "Contoh: 1-3,5,8-10.")
    groups: list[list[int]] = []
    seen: set[int] = set()
    for raw_part in value.split(","):
        part = raw_part.strip()
        try:
            bounds = [int(number) for number in part.split("-")]
        except ValueError as exc:
            raise BackendError("invalid_page_range", "Format nomor halaman belum sesuai.", "Gunakan contoh 1-3,5,8-10.") from exc
        if len(bounds) not in (1, 2):
            raise BackendError("invalid_page_range", "Format nomor halaman belum sesuai.", "Gunakan contoh 1-3,5,8-10.")
        start = bounds[0]
        end = bounds[-1]
        if start < 1 or end < start or end > page_count:
            raise BackendError(
                "page_range_out_of_bounds",
                f"Rentang halaman harus berada antara 1 dan {page_count}.",
                "Periksa jumlah halaman pada file sumber.",
            )
        group = list(range(start - 1, end))
        if any(index in seen for index in group):
            raise BackendError("duplicate_page_range", "Rentang halaman berisi nomor yang berulang.")
        seen.update(group)
        groups.append(group)
    return groups


def require_option(job: ConversionJob, name: str, *, label: str | None = None) -> str:
    value = str(job.options.get(name, "")).strip()
    if not value:
        raise BackendError(f"{name}_required", f"{label or name} belum diisi.")
    return value


def option_int(job: ConversionJob, name: str, default: int, minimum: int, maximum: int) -> int:
    try:
        value: Any = int(job.options.get(name, default))
    except (TypeError, ValueError) as exc:
        raise BackendError("invalid_option", f"Nilai {name} tidak valid.") from exc
    if not minimum <= value <= maximum:
        raise BackendError("invalid_option", f"Nilai {name} harus antara {minimum} dan {maximum}.")
    return value
