"""Tool-specific setup page with shared file, output, and validation controls."""

from __future__ import annotations

import os
import re
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from app.ui.components.common import default_output_directory
from app.ui.components.tool_options import ToolOptions
from app.ui.job_state import JobViewState
from app.ui.tool_catalog import TOOL_BY_NAME, ToolDefinition


def styled_label(text: str, object_name: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName(object_name)
    return label


class FileDropList(QFrame):
    files_dropped = Signal(list)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("fileDropList")
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:
        paths = [url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()]
        self.files_dropped.emit(paths)
        event.acceptProposedAction()


class JobPanel(QWidget):
    """A reusable detail page whose fields are selected by tool metadata."""

    close_requested = Signal()
    run_requested = Signal(object)
    cancel_requested = Signal()
    job_state_changed = Signal(str)
    open_output_requested = Signal(str)
    open_folder_requested = Signal(str)
    dependency_help_requested = Signal()

    def __init__(
        self,
        tool_name: str,
        initial_files: list[str] | None = None,
        output_directory: str = "",
        open_output: bool = True,
        libreoffice_path: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.tool: ToolDefinition = TOOL_BY_NAME[tool_name]
        self.files: list[str] = []
        self._has_custom_name = False
        self.backend_job_id: str | None = None
        self.libreoffice_path = libreoffice_path
        self.state = JobViewState.READY
        self.setObjectName("jobPage")
        self._build_ui(output_directory, open_output)
        self._add_files(initial_files or [])

    def _build_ui(self, output_directory: str, open_output: bool) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 18, 24, 12)
        root.setSpacing(10)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("scrollContents")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(2, 3, 9, 12)
        layout.setSpacing(12)

        title = styled_label(self.tool.name, "pageTitle")
        subtitle = styled_label(self.tool.guidance, "mutedText")
        subtitle.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(subtitle)
        if self.tool.key in {"word_to_pdf", "excel_to_pdf", "powerpoint_to_pdf"}:
            self._add_libreoffice_notice(layout)

        self.file_drop = FileDropList()
        drop_layout = QVBoxLayout(self.file_drop)
        drop_layout.setContentsMargins(14, 12, 14, 12)
        drop_layout.setSpacing(8)
        drop_head = QHBoxLayout()
        drop_head.addWidget(styled_label("File sumber", "sectionHeading"))
        drop_head.addStretch(1)
        self.file_count = styled_label("Belum ada file", "tinyMuted")
        drop_head.addWidget(self.file_count)
        drop_layout.addLayout(drop_head)

        self.file_list = QListWidget()
        self.file_list.setObjectName("fileList")
        self.file_list.setMinimumHeight(104)
        self.file_list.setMaximumHeight(185)
        self.file_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        if self.tool.ordered_files:
            self.file_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
            self.file_list.model().rowsMoved.connect(self._sync_order_from_list)
        self.empty_files_hint = styled_label(
            "Seret file ke area ini atau pilih dari komputer.", "emptyFilesHint"
        )
        self.empty_files_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_files_hint.setMinimumHeight(76)
        drop_layout.addWidget(self.file_list)
        drop_layout.addWidget(self.empty_files_hint)

        file_actions = QHBoxLayout()
        add_button = QPushButton("Tambah file")
        add_button.setObjectName("secondaryButton")
        add_button.clicked.connect(self._choose_files)
        file_actions.addWidget(add_button)
        self.remove_selected_button = QPushButton("Hapus pilihan")
        self.remove_selected_button.setObjectName("quietButton")
        self.remove_selected_button.setToolTip(
            "Hapus file dari daftar proses; file asli di komputer tidak dihapus."
        )
        self.remove_selected_button.clicked.connect(self._remove_selected)
        file_actions.addWidget(self.remove_selected_button)
        self.clear_files_button = QPushButton("Kosongkan daftar")
        self.clear_files_button.setObjectName("quietButton")
        self.clear_files_button.setToolTip(
            "Kosongkan semua file dari daftar; file asli di komputer tidak dihapus."
        )
        self.clear_files_button.clicked.connect(self._clear_files)
        file_actions.addWidget(self.clear_files_button)
        self.up_button = QPushButton("Naik")
        self.up_button.setObjectName("quietButton")
        self.up_button.clicked.connect(lambda _checked=False: self._move_selected(-1))
        file_actions.addWidget(self.up_button)
        self.down_button = QPushButton("Turun")
        self.down_button.setObjectName("quietButton")
        self.down_button.clicked.connect(lambda _checked=False: self._move_selected(1))
        file_actions.addWidget(self.down_button)
        file_actions.addStretch(1)
        drop_layout.addLayout(file_actions)
        self.file_error = styled_label("", "warningText")
        self.file_error.setWordWrap(True)
        self.file_error.hide()
        drop_layout.addWidget(self.file_error)
        self.file_drop.files_dropped.connect(self._add_files)
        self.file_list.itemSelectionChanged.connect(self._update_order_controls)
        layout.addWidget(self.file_drop)

        options_card = QFrame()
        options_card.setObjectName("surface")
        options_layout = QVBoxLayout(options_card)
        options_layout.setContentsMargins(16, 13, 16, 14)
        options_layout.setSpacing(8)
        options_layout.addWidget(styled_label("Pengaturan alat", "sectionHeading"))
        self.tool_options = ToolOptions(self.tool, options_card)
        for field_name, field in self.tool_options.fields.items():
            setattr(self, field_name, field)
        if self.tool_options.password_confirm is not None:
            self.password_confirm = self.tool_options.password_confirm
        if hasattr(self, "split_mode"):
            self.split_mode.currentIndexChanged.connect(self._update_split_output_mode)
        options_layout.addWidget(self.tool_options)
        layout.addWidget(options_card)

        output_card = QFrame()
        output_card.setObjectName("surface")
        output_layout = QVBoxLayout(output_card)
        output_layout.setContentsMargins(16, 13, 16, 13)
        output_layout.setSpacing(8)
        output_layout.addWidget(styled_label("Penyimpanan hasil", "sectionHeading"))
        output_row = QHBoxLayout()
        self.output_path = QLineEdit(output_directory or default_output_directory())
        self.output_path.setObjectName("inputField")
        self.output_path.setPlaceholderText("Pilih folder penyimpanan")
        output_row.addWidget(self.output_path, 1)
        browse = QPushButton("Pilih folder")
        browse.setObjectName("secondaryButton")
        browse.clicked.connect(self._choose_output)
        output_row.addWidget(browse)
        output_layout.addLayout(output_row)

        name_row = QHBoxLayout()
        self.output_name_label = styled_label(self._output_name_label(), "mutedText")
        name_row.addWidget(self.output_name_label)
        self.output_name = QLineEdit(self._default_output_name())
        self.output_name.setObjectName("inputField")
        self.output_name.textEdited.connect(lambda _text: setattr(self, "_has_custom_name", True))
        name_row.addWidget(self.output_name, 1)
        output_layout.addLayout(name_row)
        self.output_name.setVisible(self._uses_output_name())
        self.output_name_label.setVisible(self._uses_output_name())
        self.output_hint = styled_label(self._output_hint(), "tinyMuted")
        self.output_hint.setWordWrap(True)
        output_layout.addWidget(self.output_hint)
        self.open_output = QCheckBox("Buka folder output setelah selesai")
        self.open_output.setChecked(open_output)
        output_layout.addWidget(self.open_output)
        layout.addWidget(output_card)
        self.configuration_widgets = (self.file_drop, options_card, output_card)

        self.status_panel = QFrame()
        self.status_panel.setObjectName("statusPanel")
        status_layout = QVBoxLayout(self.status_panel)
        status_layout.setContentsMargins(12, 9, 12, 9)
        self.status_label = styled_label("Siap memeriksa file dan pengaturan.", "statusText")
        self.status_label.setWordWrap(True)
        status_header = QHBoxLayout()
        status_header.addWidget(self.status_label, 1)
        self.progress_value_label = styled_label("", "progressValue")
        self.progress_value_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        status_header.addWidget(self.progress_value_label)
        status_layout.addLayout(status_header)
        self.progress = QProgressBar()
        self.progress.setObjectName("jobProgress")
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.hide()
        status_layout.addWidget(self.progress)
        status_actions = QHBoxLayout()
        self.cancel_job_button = QPushButton("Batalkan proses")
        self.cancel_job_button.setObjectName("dangerButton")
        self.cancel_job_button.clicked.connect(self.cancel_requested.emit)
        status_actions.addWidget(self.cancel_job_button)
        status_actions.addStretch(1)
        self.open_result_button = QPushButton("Buka file hasil")
        self.open_result_button.setObjectName("secondaryButton")
        self.open_result_button.clicked.connect(self._open_first_result)
        status_actions.addWidget(self.open_result_button)
        self.open_result_folder_button = QPushButton("Buka folder")
        self.open_result_folder_button.setObjectName("secondaryButton")
        self.open_result_folder_button.clicked.connect(self._open_result_folder)
        status_actions.addWidget(self.open_result_folder_button)
        status_layout.addLayout(status_actions)
        self.cancel_job_button.hide()
        self.open_result_button.hide()
        self.open_result_folder_button.hide()
        self.status_panel.hide()
        layout.addWidget(self.status_panel)
        layout.addStretch(1)
        scroll.setWidget(content)
        root.addWidget(scroll, 1)

        actions = QHBoxLayout()
        self.validation_hint = styled_label(self._requirement_text(), "tinyMuted")
        self.validation_hint.setWordWrap(True)
        actions.addWidget(self.validation_hint, 1)
        cancel = QPushButton("Kembali")
        cancel.setObjectName("quietButton")
        cancel.clicked.connect(lambda _checked=False: self.close_requested.emit())
        actions.addWidget(cancel)
        self.start_button = QPushButton("Mulai proses")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self._start_job)
        actions.addWidget(self.start_button)
        root.addLayout(actions)

    def _add_libreoffice_notice(self, layout: QVBoxLayout) -> None:
        notice = QFrame()
        notice.setObjectName("dependencyNotice")
        row = QHBoxLayout(notice)
        row.setContentsMargins(12, 8, 12, 8)
        message = QLabel()
        message.setWordWrap(True)
        if self.libreoffice_path:
            message.setObjectName("statusSuccess")
            message.setText("DocuConvert siap mengonversi dokumen Office.")
            row.addWidget(message, 1)
        else:
            message.setObjectName("statusWarning")
            message.setText(
                "Komponen konversi DocuConvert belum tersedia. Periksa instalasi aplikasi."
            )
            row.addWidget(message, 1)
            help_button = QPushButton("Petunjuk")
            help_button.setObjectName("secondaryButton")
            help_button.clicked.connect(self.dependency_help_requested.emit)
            row.addWidget(help_button)
        layout.addWidget(notice)

    def _requirement_text(self) -> str:
        if self.tool.key == "merge_pdf":
            return "Pilih minimal dua PDF. Tarik baris atau gunakan tombol Naik/Turun untuk mengatur urutan." \
                if self.tool.ordered_files else "Pilih minimal dua file PDF."
        if self.tool.key == "image_to_pdf":
            return "Urutan gambar menentukan susunan halaman. Tarik baris atau gunakan tombol Naik/Turun."
        return "Periksa pengaturan, lalu mulai proses."

    def _uses_output_name(self) -> bool:
        return True

    def _output_name_label(self) -> str:
        if self.tool.key == "split_pdf" and self.split_mode.currentData() == "ranges":
            return "Awalan nama file"
        return "Awalan nama gambar" if self.tool.key == "pdf_to_image" else "Nama file hasil"

    def _update_split_output_mode(self) -> None:
        self.output_name_label.setText(self._output_name_label())
        if not self._has_custom_name:
            self.output_name.setText(self._suggest_output_name())
        self.output_hint.setText(self._output_hint())

    def _output_hint(self) -> str:
        if self.tool.key in {"word_to_pdf", "excel_to_pdf", "powerpoint_to_pdf"}:
            return (
                "Kosongkan untuk memakai nama tiap file sumber. Nama khusus diberi nomor untuk banyak file."
            )
        if self.tool.key == "pdf_to_image":
            return "Setiap halaman menjadi gambar terpisah dengan nomor halaman pada namanya."
        if self.tool.key == "split_pdf" and self.split_mode.currentData() == "ranges":
            return "Setiap rentang menghasilkan PDF terpisah dengan nomor halaman pada namanya."
        return (
            "Nama mengikuti file sumber dan dapat diubah. "
            "Jika sudah ada, nomor ditambahkan otomatis."
        )

    def _default_output_name(self) -> str:
        suffixes = {
            "merge_pdf": "dokumen_merged.pdf",
            "split_pdf": "halaman_terpilih.pdf",
            "compress_pdf": "dokumen_compressed.pdf",
            "image_to_pdf": "gambar.pdf",
            "pdf_to_image": "halaman",
            "pdf_to_word": "dokumen.docx",
            "rotate_pdf": "dokumen_diputar.pdf",
            "delete_pages": "halaman_dihapus.pdf",
            "watermark_pdf": "dokumen_watermark.pdf",
            "protect_pdf": "dokumen_terkunci.pdf",
        }
        return suffixes.get(self.tool.key, "dokumen_converted.pdf")

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Pilih file sumber", "", self._file_filter()
        )
        self._add_files(paths)

    def _file_filter(self) -> str:
        patterns = " ".join(f"*{extension}" for extension in sorted(self.tool.extensions))
        return f"File didukung ({patterns});;Semua file (*.*)"

    def _add_files(self, paths: list[str]) -> None:
        accepted: list[str] = []
        rejected: list[str] = []
        for raw_path in paths:
            path = Path(raw_path)
            if (
                not path.is_file()
                or path.suffix.lower() not in self.tool.extensions
                or not os.access(path, os.R_OK)
            ):
                rejected.append(path.name or raw_path)
                continue
            normalized = str(path.resolve())
            if normalized not in self.files and (
                self.tool.multiple_files or (not self.files and not accepted)
            ):
                accepted.append(normalized)
        self.files.extend(accepted)
        if accepted and not self._has_custom_name and self._uses_output_name():
            self.output_name.setText(self._suggest_output_name())
        self._refresh_file_list()
        if rejected:
            self.file_error.setText("File tidak didukung atau hanya satu file yang dapat dipilih: " + ", ".join(rejected))
            self.file_error.show()
        else:
            self.file_error.hide()

    def _suggest_output_name(self) -> str:
        if not self.files:
            return self._default_output_name()
        stem = Path(self.files[0]).stem
        if (
            self.tool.key in {"word_to_pdf", "excel_to_pdf", "powerpoint_to_pdf"}
            and len(self.files) > 1
        ):
            return ""
        if self.tool.key == "pdf_to_image" or (
            self.tool.key == "split_pdf" and self.split_mode.currentData() == "ranges"
        ):
            return stem
        return f"{stem}{'.docx' if self.tool.key == 'pdf_to_word' else '.pdf'}"

    def _refresh_file_list(self) -> None:
        self.file_list.blockSignals(True)
        self.file_list.clear()
        for path in self.files:
            file_path = Path(path)
            size = self._format_file_size(file_path.stat().st_size)
            item = QListWidgetItem(
                f"{file_path.name}  ·  {file_path.suffix[1:].upper()}  ·  {size}"
            )
            item.setToolTip(path)
            item.setData(Qt.ItemDataRole.UserRole, path)
            self.file_list.addItem(item)
        self.file_list.blockSignals(False)
        has_files = bool(self.files)
        self.file_list.setVisible(has_files)
        self.empty_files_hint.setVisible(not has_files)
        self.file_count.setText(f"{len(self.files)} file dipilih" if has_files else "Belum ada file")
        self.remove_selected_button.setEnabled(self.file_list.currentRow() >= 0)
        self.clear_files_button.setEnabled(has_files)
        self._update_order_controls()

    @staticmethod
    def _format_file_size(size: int) -> str:
        if size < 1024:
            return f"{size} B"
        if size < 1024**2:
            return f"{size / 1024:.0f} KB"
        return f"{size / (1024**2):.1f} MB"

    def _sync_order_from_list(self, *_args: object) -> None:
        self.files = [
            self.file_list.item(index).data(Qt.ItemDataRole.UserRole)
            for index in range(self.file_list.count())
        ]
        if not self._has_custom_name:
            self.output_name.setText(self._suggest_output_name())
        self._refresh_file_list()

    def _update_order_controls(self) -> None:
        can_move = self.tool.ordered_files and self.file_list.currentRow() >= 0
        row = self.file_list.currentRow()
        self.remove_selected_button.setEnabled(row >= 0)
        self.up_button.setVisible(self.tool.ordered_files)
        self.down_button.setVisible(self.tool.ordered_files)
        self.up_button.setEnabled(bool(can_move and row > 0))
        self.down_button.setEnabled(bool(can_move and row < len(self.files) - 1))

    def _remove_selected(self) -> None:
        row = self.file_list.currentRow()
        if 0 <= row < len(self.files):
            self.files.pop(row)
            if not self.files:
                self._has_custom_name = False
                if self._uses_output_name():
                    self.output_name.setText(self._default_output_name())
            elif not self._has_custom_name and self._uses_output_name():
                self.output_name.setText(self._suggest_output_name())
            self._refresh_file_list()
            self._reset_completion_if_empty()

    def _clear_files(self) -> None:
        self.files.clear()
        self._has_custom_name = False
        self.file_error.hide()
        if self._uses_output_name():
            self.output_name.setText(self._default_output_name())
        self._refresh_file_list()
        self._reset_completion_if_empty()

    def _reset_completion_if_empty(self) -> None:
        if self.files or self.state != JobViewState.COMPLETED:
            return
        self._set_view_state(JobViewState.READY)
        self.status_panel.hide()
        self.progress.hide()
        self.progress_value_label.hide()
        self.start_button.setText("Mulai proses")
        self.start_button.setEnabled(True)

    def _move_selected(self, direction: int) -> None:
        row = self.file_list.currentRow()
        target = row + direction
        if row < 0 or target < 0 or target >= len(self.files):
            return
        self.files[row], self.files[target] = self.files[target], self.files[row]
        self._refresh_file_list()
        self.file_list.setCurrentRow(target)

    def _choose_output(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Pilih folder output", self.output_path.text()
        )
        if path:
            self.output_path.setText(path)

    def _validate_page_ranges(self, field: QLineEdit, label: str) -> bool:
        value = field.text().strip()
        pattern = r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*"
        if not value or not re.fullmatch(pattern, value):
            self._show_validation_error(
                f"{label}: gunakan angka dan rentang seperti 1-3,5,8-10.", field
            )
            field.setFocus()
            return False
        for part in value.split(","):
            limits = [int(number) for number in part.split("-")]
            if any(number < 1 for number in limits) or (len(limits) == 2 and limits[0] > limits[1]):
                self._show_validation_error(
                    f"{label}: rentang harus dimulai dari halaman 1 dan urut naik.", field
                )
                field.setFocus()
                return False
        return True

    def _show_validation_error(self, message: str, field: QWidget | None = None) -> None:
        self._set_configuration_enabled(True)
        self.status_panel.show()
        self._set_status_style("statusError")
        self.status_label.setText(message)
        self.progress.hide()
        self.progress_value_label.hide()
        self.cancel_job_button.hide()
        self.open_result_button.hide()
        self.open_result_folder_button.hide()
        if field is not None:
            field.setFocus()

    def _start_job(self) -> None:
        minimum_files = 2 if self.tool.key == "merge_pdf" else 1
        if len(self.files) < minimum_files:
            self._show_validation_error(
                "Tambahkan minimal dua file PDF untuk menggabungkan dokumen."
                if minimum_files == 2 else "Tambahkan setidaknya satu file yang didukung."
            )
            return
        if self.tool.key in {"split_pdf", "rotate_pdf", "delete_pages"}:
            if not self._validate_page_ranges(self.page_ranges, "Rentang halaman"):
                return
        if self.tool.key == "pdf_to_image" and self.image_page_range.text().strip():
            if not self._validate_page_ranges(self.image_page_range, "Halaman"):
                return
        if self.tool.key == "watermark_pdf" and not self.watermark_text.text().strip():
            self._show_validation_error(
                "Teks watermark diperlukan sebelum melanjutkan.", self.watermark_text
            )
            return
        if self.tool.key == "protect_pdf":
            if len(self.password.text()) < 6:
                self._show_validation_error(
                    "Password harus terdiri dari minimal 6 karakter.", self.password
                )
                return
            if self.password.text() != self.password_confirm.text():
                self._show_validation_error(
                    "Password dan konfirmasi belum sama.", self.password_confirm
                )
                return
        output_directory = Path(self.output_path.text().strip())
        if not output_directory.is_dir():
            self._show_validation_error(
                "Folder output tidak ditemukan. Pilih folder yang tersedia.", self.output_path
            )
            return
        if not os.access(output_directory, os.W_OK):
            self._show_validation_error(
                "Folder output tidak dapat ditulis. Pilih folder lain yang bisa digunakan.",
                self.output_path,
            )
            return
        if not self.output_name.text().strip() and self.tool.key not in {
            "word_to_pdf", "excel_to_pdf", "powerpoint_to_pdf"
        }:
            self._show_validation_error(
                "Nama hasil diperlukan. Isi nama file atau awalan nama gambar.", self.output_name
            )
            return
        if not self._validate_output_target():
            return

        request = self._create_request()
        self.validation_hint.setObjectName("tinyMuted")
        self.validation_hint.setText(self._requirement_text())
        self.set_validating()
        self.backend_job_id = None
        self.run_requested.emit(request)

    def _validate_output_target(self) -> bool:
        output_directory = Path(self.output_path.text().strip())
        name = self.output_name.text().strip()
        if os.name == "nt" and self._uses_output_name() and re.search(r'[<>:"/\\|?*]', name):
            self._show_validation_error(
                "Nama hasil mengandung karakter yang tidak dapat digunakan di Windows.",
                self.output_name,
            )
            return False
        targets = self._output_targets(output_directory, name)
        if any(target.parent != output_directory for target in targets):
            self._show_validation_error(
                "Isi nama file saja, tanpa lokasi folder.", self.output_name,
            )
            return False
        return True

    def _output_targets(self, output_directory: Path, name: str) -> list[Path]:
        if self.tool.key in {"word_to_pdf", "excel_to_pdf", "powerpoint_to_pdf"} and not name:
            return [output_directory / f"{Path(source).stem}.pdf" for source in self.files]
        if self.tool.key == "pdf_to_image":
            extension = str(self.image_format.currentData())
            prefix = Path(name).stem if Path(name).suffix else name
            return [output_directory / f"{prefix}-001.{extension}"]
        if self.tool.key == "split_pdf" and self.split_mode.currentData() == "ranges":
            prefix = Path(name).stem if Path(name).suffix else name
            ranges = [part.strip().replace("-", "_") for part in self.page_ranges.text().split(",")]
            return [output_directory / f"{prefix}_{page_range}.pdf" for page_range in ranges]
        return [output_directory / name]

    @staticmethod
    def _numbered_output_name(name: str, index: int) -> str:
        output_path = Path(name)
        suffix = output_path.suffix
        stem = output_path.stem if suffix else output_path.name
        return f"{stem}_{index}{suffix}"

    def _create_request(self) -> dict[str, object]:
        options = self.tool_options.request_values()
        return {
            "tool_key": self.tool.key,
            "tool_name": self.tool.name,
            "sources": list(self.files),
            "output_directory": self.output_path.text().strip(),
            "output_name": self.output_name.text().strip(),
            "open_output": self.open_output.isChecked(),
            "options": options,
        }

    def set_validating(self) -> None:
        self._set_view_state(JobViewState.VALIDATING)
        self.status_panel.show()
        self._set_status_style("statusText")
        self.status_label.setText("Memeriksa file dan pengaturan…")
        self.progress.setRange(0, 0)
        self.progress.setFormat("")
        self.progress_value_label.setText("Memeriksa")
        self.progress_value_label.show()
        self.progress.show()
        self.cancel_job_button.hide()
        self.open_result_button.hide()
        self.open_result_folder_button.hide()
        self.start_button.setText("Memeriksa…")
        self.start_button.setEnabled(False)
        self._set_configuration_enabled(False)

    def set_processing(self, progress: int | None = None, message: str = "Sedang memproses file…") -> None:
        self._set_view_state(JobViewState.PROCESSING)
        self.status_panel.show()
        self._set_status_style("statusText")
        self.status_label.setText(message)
        if progress is None:
            self.progress.setRange(0, 0)
            self.progress.setFormat("")
            self.progress_value_label.setText("Memproses")
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(max(0, min(progress, 100)))
            self.progress_value_label.setText(f"{max(0, min(progress, 100))}%")
        self.progress_value_label.show()
        self.progress.show()
        self.cancel_job_button.setText("Batalkan proses")
        self.cancel_job_button.setEnabled(True)
        self.cancel_job_button.show()
        self.open_result_button.hide()
        self.open_result_folder_button.hide()
        self.start_button.setText("Sedang diproses…")
        self.start_button.setEnabled(False)
        self._set_configuration_enabled(False)

    def set_unavailable(self, message: str) -> None:
        self._set_view_state(JobViewState.UNAVAILABLE)
        self._set_configuration_enabled(True)
        self.status_panel.show()
        self._set_status_style("statusWarning")
        self.status_label.setText(message)
        self.progress.hide()
        self.progress_value_label.hide()
        self.cancel_job_button.hide()
        self.open_result_button.hide()
        self.open_result_folder_button.hide()
        self.start_button.setText("Periksa lagi")
        self.start_button.setEnabled(True)

    def set_completed(
        self, output_files: list[str], *, warnings: list[str] | None = None
    ) -> None:
        self._set_view_state(JobViewState.COMPLETED)
        self._set_configuration_enabled(True)
        self.status_panel.show()
        self._set_status_style("statusWarning" if warnings else "statusSuccess")
        details = (
            "DocuConvert selesai mengompres PDF. File hasil sudah tersedia."
            if self.tool.key == "compress_pdf"
            else "DocuConvert selesai memproses dokumen. File hasil sudah tersedia."
        )
        if warnings:
            details += " " + " ".join(warnings)
        self.status_label.setText(details)
        self.status_label.setProperty("output_files", list(output_files))
        self.progress.setRange(0, 100)
        self.progress.setValue(100)
        self.progress_value_label.setText("100%")
        self.progress_value_label.show()
        self.progress.show()
        self.cancel_job_button.hide()
        self.open_result_button.setVisible(bool(output_files))
        self.open_result_folder_button.setVisible(bool(output_files))
        self.start_button.setText("Konversi lagi")
        self.start_button.setEnabled(True)
        if self.open_output.isChecked() and output_files:
            self.open_folder_requested.emit(str(Path(output_files[0]).parent))

    def set_failed(self, message: str, *, recovery: str = "Periksa file dan pengaturan, lalu coba lagi.") -> None:
        self._set_view_state(JobViewState.FAILED)
        self._set_configuration_enabled(True)
        details = f"{message}\n{recovery}"
        self.status_panel.show()
        self._set_status_style("statusError")
        self.status_label.setText(details)
        self.progress.hide()
        self.progress_value_label.hide()
        self.cancel_job_button.hide()
        self.open_result_button.hide()
        self.open_result_folder_button.hide()
        self.start_button.setText("Coba lagi")
        self.start_button.setEnabled(True)

    def set_cancelled(self, message: str = "Proses dibatalkan. File sumber tetap aman.") -> None:
        self._set_view_state(JobViewState.CANCELLED)
        self._set_configuration_enabled(True)
        self.status_panel.show()
        self._set_status_style("statusWarning")
        self.status_label.setText(message)
        self.progress.hide()
        self.progress_value_label.hide()
        self.cancel_job_button.hide()
        self.open_result_button.hide()
        self.open_result_folder_button.hide()
        self.start_button.setText("Coba lagi")
        self.start_button.setEnabled(True)

    def request_cancellation(self) -> None:
        self.status_label.setText("Permintaan pembatalan dikirim. Menunggu proses berhenti…")
        self.cancel_job_button.setText("Menunggu…")
        self.cancel_job_button.setEnabled(False)

    def _set_status_style(self, object_name: str) -> None:
        self.status_label.setObjectName(object_name)
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)

    def _set_view_state(self, state: JobViewState) -> None:
        self.state = state
        self.job_state_changed.emit(state.value)

    def _set_configuration_enabled(self, enabled: bool) -> None:
        for widget in getattr(self, "configuration_widgets", ()):
            widget.setEnabled(enabled)

    def _open_first_result(self) -> None:
        paths = self.status_label.property("output_files")
        if paths:
            self.open_output_requested.emit(str(paths[0]))

    def _open_result_folder(self) -> None:
        paths = self.status_label.property("output_files")
        if paths:
            self.open_folder_requested.emit(str(Path(paths[0]).parent))
