"""Drag-and-drop surface with a native file picker action."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QIcon
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from app.ui.components.common import icon_path


class DropZone(QFrame):
    files_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("dropZone")
        self.setAcceptDrops(True)
        self.setMinimumHeight(186)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(9)

        illustration = QLabel()
        illustration.setObjectName("dropIllustration")
        illustration.setPixmap(QIcon(str(icon_path("drop.svg"))).pixmap(62, 56))
        illustration.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(illustration)

        title = QLabel("Taruh file di sini")
        title.setObjectName("dropTitle")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel("Pilih alat lebih dulu, atau lanjutkan dari kartu di bawah")
        subtitle.setObjectName("mutedText")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(subtitle)

        self.choose_button = QPushButton("Pilih file")
        self.choose_button.setObjectName("primaryButton")
        self.choose_button.setCursor(Qt.CursorShape.PointingHandCursor)
        layout.addWidget(self.choose_button, alignment=Qt.AlignmentFlag.AlignCenter)

        formats = QLabel("DOCX  ·  XLSX  ·  PPTX  ·  PDF  ·  JPG  ·  PNG")
        formats.setObjectName("formatsLabel")
        formats.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(formats)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self.files_dropped.emit(paths)
        event.acceptProposedAction()
