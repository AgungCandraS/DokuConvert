"""Shared UI helpers for local resources and tactile surfaces."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QStandardPaths
from PySide6.QtWidgets import QFrame, QWidget


def icon_path(filename: str) -> Path:
    return Path(__file__).parent.parent / "resources" / "icons" / filename


def default_output_directory() -> str:
    documents = QStandardPaths.writableLocation(
        QStandardPaths.StandardLocation.DocumentsLocation
    )
    candidate = Path(documents) if documents else Path.home()
    return str(candidate if candidate.is_dir() else Path.home())


def card_frame(parent: QWidget | None = None, *, object_name: str = "surface") -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName(object_name)
    return frame
