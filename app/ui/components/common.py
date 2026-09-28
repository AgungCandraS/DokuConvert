"""Shared UI helpers for local resources and tactile surfaces."""

from pathlib import Path

from PySide6.QtWidgets import QFrame


def icon_path(filename: str) -> Path:
    return Path(__file__).parent.parent / "resources" / "icons" / filename


def card_frame(parent: QWidget | None = None, *, object_name: str = "surface") -> QFrame:
    frame = QFrame(parent)
    frame.setObjectName(object_name)
    return frame
