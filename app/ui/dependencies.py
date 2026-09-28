"""UI compatibility wrapper for backend dependency detection."""

from app.backend.infrastructure.libreoffice_runner import (
    find_libreoffice,
    is_bundled_libreoffice,
)

__all__ = ["find_libreoffice", "is_bundled_libreoffice"]
