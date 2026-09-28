"""History screen and rows for local conversion metadata."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HistoryRow(QWidget):
    open_output = Signal(str)
    open_folder = Signal(str)
    retry_job = Signal(str, object)

    def __init__(self, entry: dict[str, object], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("historyRow")
        row = QHBoxLayout(self)
        row.setContentsMargins(12, 9, 12, 9)
        row.setSpacing(12)
        summary = QVBoxLayout()
        summary.setSpacing(3)
        name = QLabel(str(entry.get("tool_name", "Proses dokumen")))
        name.setObjectName("historyTitle")
        summary.addWidget(name)
        sources = [Path(path).name for path in entry.get("sources", [])]
        source_text = ", ".join(sources[:2])
        if len(sources) > 2:
            source_text += f" dan {len(sources) - 2} file lainnya"
        source_label = QLabel(source_text or "Tidak ada file sumber")
        source_label.setObjectName("tinyMuted")
        source_label.setToolTip("\n".join(sources))
        summary.addWidget(source_label)
        date_label = QLabel(self._format_date(str(entry.get("created_at", ""))))
        date_label.setObjectName("tinyMuted")
        summary.addWidget(date_label)
        row.addLayout(summary, 1)

        state = str(entry.get("status", "failed"))
        status_label = QLabel(self._status_text(state))
        status_label.setObjectName(f"historyStatus_{state}")
        status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_label.setMinimumWidth(92)
        row.addWidget(status_label)

        outputs = [str(path) for path in entry.get("outputs", [])]
        if outputs:
            open_button = QPushButton("Buka hasil")
            open_button.setObjectName("secondaryButton")
            open_button.setAccessibleName("Buka hasil proses")
            open_button.clicked.connect(lambda _checked=False: self.open_output.emit(outputs[0]))
            row.addWidget(open_button)
            folder_button = QPushButton("Folder")
            folder_button.setObjectName("quietButton")
            folder_button.setAccessibleName("Buka folder hasil")
            folder_button.clicked.connect(
                lambda _checked=False: self.open_folder.emit(str(Path(outputs[0]).parent))
            )
            row.addWidget(folder_button)

        retry_button = QPushButton("Ulangi")
        retry_button.setObjectName("quietButton")
        retry_button.setAccessibleName("Ulangi pengaturan proses")
        retry_button.setEnabled(bool(entry.get("sources")))
        retry_button.clicked.connect(
            lambda _checked=False: self.retry_job.emit(
                str(entry.get("tool_key", "")), list(entry.get("sources", []))
            )
        )
        row.addWidget(retry_button)

    @staticmethod
    def _format_date(value: str) -> str:
        try:
            created = datetime.fromisoformat(value).astimezone()
            return created.strftime("%d %b %Y, %H:%M")
        except ValueError:
            return value or "Waktu tidak tersedia"

    @staticmethod
    def _status_text(status: str) -> str:
        return {
            "completed": "Selesai",
            "failed": "Gagal",
            "cancelled": "Dibatalkan",
        }.get(status, "Diproses")


class HistoryPage(QWidget):
    open_output = Signal(str)
    open_folder = Signal(str)
    retry_job = Signal(str, object)
    clear_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        header = QHBoxLayout()
        heading = QVBoxLayout()
        heading.setSpacing(3)
        title = QLabel("Riwayat")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Daftar proses yang pernah dijalankan.")
        subtitle.setObjectName("mutedText")
        heading.addWidget(title)
        heading.addWidget(subtitle)
        header.addLayout(heading)
        header.addStretch(1)
        self.filter = QComboBox()
        self.filter.addItem("Semua proses", "all")
        self.filter.addItem("Berhasil", "completed")
        self.filter.addItem("Gagal", "failed")
        self.filter.addItem("Dibatalkan", "cancelled")
        self.filter.currentIndexChanged.connect(self._render)
        header.addWidget(self.filter)
        self.clear_button = QPushButton("Hapus riwayat")
        self.clear_button.setObjectName("quietButton")
        self.clear_button.clicked.connect(self.clear_requested.emit)
        header.addWidget(self.clear_button)
        layout.addLayout(header)

        self.list = QListWidget()
        self.list.setObjectName("historyList")
        self.list.setSpacing(6)
        self.list.setFrameShape(QFrame.Shape.NoFrame)
        layout.addWidget(self.list, 1)
        self.empty_state = QFrame()
        self.empty_state.setObjectName("surface")
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(24, 24, 24, 24)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_title = QLabel("Belum ada proses")
        empty_title.setObjectName("sectionHeading")
        empty_copy = QLabel("Proses yang selesai, gagal, atau dibatalkan akan muncul di sini.")
        empty_copy.setObjectName("mutedText")
        empty_copy.setWordWrap(True)
        empty_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_copy)
        self.empty_copy = empty_copy
        layout.addWidget(self.empty_state, 1)
        self._entries: list[dict[str, object]] = []

    def set_entries(self, entries: list[dict[str, object]]) -> None:
        self._entries = entries
        self._render()

    def _render(self, *_args: object) -> None:
        selected_state = self.filter.currentData()
        visible = [
            entry for entry in self._entries
            if selected_state == "all" or entry.get("status") == selected_state
        ]
        self.list.clear()
        for entry in visible:
            item = QListWidgetItem()
            widget = HistoryRow(entry)
            widget.open_output.connect(self.open_output)
            widget.open_folder.connect(self.open_folder)
            widget.retry_job.connect(self.retry_job)
            item.setSizeHint(widget.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, widget)
        self.list.setVisible(bool(visible))
        self.empty_state.setVisible(not visible)
        if self._entries and not visible:
            self.empty_copy.setText("Tidak ada proses yang cocok dengan filter ini.")
        else:
            self.empty_copy.setText("Proses yang selesai, gagal, atau dibatalkan akan muncul di sini.")
        self.clear_button.setEnabled(bool(self._entries))
