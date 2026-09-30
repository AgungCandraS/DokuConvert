"""Desktop shell and navigation for the DocuConvert frontend."""

from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import QSettings, QSize, Qt, QUrl
from PySide6.QtGui import QColor, QDesktopServices, QIcon, QPalette
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.backend.domain.enums import JobStatus
from app.backend.infrastructure.update_service import UpdateRelease
from app.ui.components.common import card_frame, default_output_directory, icon_path
from app.ui.components.drop_zone import DropZone
from app.ui.components.tool_card import ToolCard
from app.ui.controllers.job_controller import JobController
from app.ui.controllers.update_controller import UpdateController, launch_update
from app.ui.dependencies import find_libreoffice
from app.ui.history_page import HistoryPage
from app.ui.job_panel import JobPanel
from app.ui.themes import DARK_STYLESHEET, LIGHT_STYLESHEET
from app.ui.tool_catalog import FEATURED_TOOL_KEYS, TOOL_BY_KEY, TOOLS
from app.version import VERSION


def styled_label(text: str, object_name: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName(object_name)
    return label


class MainWindow(QMainWindow):
    """Primary navigation, preferences, and the shared tool host."""

    def __init__(self, job_controller: JobController | None = None) -> None:
        super().__init__()
        self.setWindowTitle("DocuConvert | Pengelola Dokumen")
        self.setWindowIcon(QIcon(str(icon_path("app-icon.png"))))
        self.resize(1440, 920)
        self.setMinimumSize(1120, 760)
        self.settings = QSettings("DocuConvert", "DocuConvert")
        self.job_controller = job_controller
        self._migrate_legacy_history()
        self.libreoffice_path = find_libreoffice(
            self.settings.value("libreoffice_executable") or None
        )
        self.dark_mode = self.settings.value("theme", "light") == "dark"
        self.job_page: JobPanel | None = None
        self.return_page: QWidget | None = None
        self.return_breadcrumb = "DocuConvert   /   Beranda"
        self._build_ui()
        if self.job_controller is not None:
            self.job_controller.runtime.history.limit = self._selected_history_limit()
            self.job_controller.job_updated.connect(self._handle_backend_event)
            self.job_controller.history_changed.connect(self._refresh_history)
            self.job_controller.submission_failed.connect(self._handle_submission_failure)
            self._refresh_history()
        self._apply_theme()
        self.available_update: UpdateRelease | None = None
        self.update_package: Path | None = None
        self._notified_version = ""
        self.updates = UpdateController(self)
        self.updates.checked.connect(self._update_checked)
        self.updates.downloaded.connect(self._update_downloaded)
        self.updates.failed.connect(self._update_failed)
        self.updates.progress.connect(self._update_progress)
        self.updates.busy_changed.connect(self._update_busy)

    def _migrate_legacy_history(self) -> None:
        if self.job_controller is None:
            return
        raw_history = self.settings.value("job_history", "[]", type=str)
        try:
            legacy_entries = json.loads(raw_history)
        except (TypeError, json.JSONDecodeError):
            legacy_entries = []
        self.job_controller.import_legacy_history(legacy_entries)
        self.settings.remove("job_history")

    def _build_ui(self) -> None:
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(228)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(17, 22, 17, 16)
        side.setSpacing(7)
        side.addLayout(self._brand_row())
        side.addSpacing(26)
        side.addWidget(styled_label("NAVIGASI", "sectionLabel"))
        self.nav_buttons: dict[str, QPushButton] = {}
        for label, icon in (
            ("Beranda", "nav-home.svg"),
            ("Semua alat", "nav-tools.svg"),
            ("Riwayat", "nav-history.svg"),
        ):
            self._add_navigation_button(side, label, icon)
        side.addSpacing(18)
        side.addWidget(styled_label("PREFERENSI", "sectionLabel"))
        self._add_navigation_button(side, "Pengaturan", "nav-settings.svg")
        self._add_navigation_button(side, "Tentang", "nav-about.svg")
        side.addStretch(1)

        privacy = card_frame(object_name="privacyCard")
        privacy_layout = QVBoxLayout(privacy)
        privacy_layout.setContentsMargins(12, 12, 12, 12)
        privacy_layout.setSpacing(5)
        privacy_layout.addWidget(styled_label("FILE TETAP PRIVAT", "privacyTitle"))
        privacy_copy = styled_label("Dirancang untuk memproses file di perangkat.", "tinyMuted")
        privacy_copy.setWordWrap(True)
        privacy_layout.addWidget(privacy_copy)
        side.addWidget(privacy)
        side.addWidget(
            styled_label(f"Versi {VERSION}", "tinyMuted"),
            alignment=Qt.AlignmentFlag.AlignHCenter,
        )
        shell.addWidget(sidebar)

        content = QWidget()
        content.setObjectName("content")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(28, 20, 28, 14)
        content_layout.setSpacing(14)
        header = QHBoxLayout()
        self.breadcrumb = styled_label("DocuConvert   /   Beranda", "breadcrumb")
        header.addWidget(self.breadcrumb)
        header.addStretch(1)
        theme_button = QPushButton("Tema")
        theme_button.setObjectName("secondaryButton")
        theme_button.setIcon(QIcon(str(icon_path("nav-theme.svg"))))
        theme_button.setIconSize(QSize(17, 17))
        theme_button.setToolTip("Ganti tema terang atau gelap")
        theme_button.setAccessibleName("Ganti tema terang atau gelap")
        theme_button.clicked.connect(self._toggle_theme)
        header.addWidget(theme_button)
        content_layout.addLayout(header)

        self.pages = QStackedWidget()
        self.pages.setObjectName("pages")
        self.dashboard = self._build_dashboard()
        self.tools_page = self._build_tools_page()
        self.other_page = self._build_other_page()
        self.pages.addWidget(self.dashboard)
        self.pages.addWidget(self.tools_page)
        self.pages.addWidget(self.other_page)
        content_layout.addWidget(self.pages, 1)

        footer = QHBoxLayout()
        footer.addWidget(styled_label("●", "statusDot"))
        self.status_label = styled_label("Siap digunakan", "statusText")
        footer.addWidget(self.status_label)
        footer.addStretch(1)
        content_layout.addLayout(footer)
        shell.addWidget(content, 1)
        self.nav_buttons["Beranda"].setChecked(True)

    def _brand_row(self) -> QHBoxLayout:
        brand_row = QHBoxLayout()
        brand_icon = QLabel()
        brand_icon.setObjectName("brandIcon")
        brand_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_icon.setPixmap(QIcon(str(icon_path("brandmark.svg"))).pixmap(38, 38))
        brand_icon.setFixedSize(44, 44)
        brand_row.addWidget(brand_icon)
        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand_text.addWidget(styled_label("DocuConvert", "brandName"))
        brand_text.addWidget(styled_label("DESKTOP", "brandSub"))
        brand_row.addLayout(brand_text)
        brand_row.addStretch(1)
        return brand_row

    def _add_navigation_button(self, layout: QVBoxLayout, label: str, icon_name: str) -> None:
        button = QPushButton(label)
        button.setObjectName("navButton")
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setIcon(QIcon(str(icon_path(icon_name))))
        button.setIconSize(QSize(18, 18))
        button.setAccessibleName(label)
        button.clicked.connect(lambda _checked=False, page=label: self._navigate(page))
        self.nav_buttons[label] = button
        layout.addWidget(button)

    def _build_dashboard(self) -> QWidget:
        page = QWidget()
        page.setObjectName("page")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(15)
        title_group = QVBoxLayout()
        title_group.setSpacing(4)
        title_group.addWidget(styled_label("Rapikan dokumen, tanpa ribet.", "pageTitle"))
        title_group.addWidget(styled_label("Pilih alat untuk mulai mengolah dokumen.", "mutedText"))
        layout.addLayout(title_group)

        self.drop_zone = DropZone()
        self.drop_zone.choose_button.clicked.connect(self._choose_files)
        self.drop_zone.files_dropped.connect(self._add_files)
        layout.addWidget(self.drop_zone)

        tools_header = QHBoxLayout()
        tools_header.addWidget(styled_label("Alat yang sering digunakan", "sectionHeading"))
        tools_header.addStretch(1)
        see_all = QPushButton("Lihat semua alat  →")
        see_all.setObjectName("textButton")
        see_all.clicked.connect(lambda _checked=False: self._navigate("Semua alat"))
        tools_header.addWidget(see_all)
        layout.addLayout(tools_header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(11)
        grid.setVerticalSpacing(10)
        for index, key in enumerate(FEATURED_TOOL_KEYS):
            card = ToolCard(TOOL_BY_KEY[key])
            card.tool_selected.connect(self._select_tool)
            grid.addWidget(card, index // 3, index % 3)
        layout.addLayout(grid)

        bottom = QHBoxLayout()
        bottom.setSpacing(12)
        activity = card_frame(object_name="surface")
        activity_layout = QVBoxLayout(activity)
        activity_layout.setContentsMargins(15, 11, 15, 11)
        activity_layout.addWidget(styled_label("Aktivitas terakhir", "sectionHeading"))
        self.activity_copy = styled_label("Belum ada aktivitas.", "tinyMuted")
        self.activity_copy.setWordWrap(True)
        activity_layout.addWidget(self.activity_copy)
        bottom.addWidget(activity, 3)
        privacy_tip = card_frame(object_name="tipCard")
        tip_layout = QVBoxLayout(privacy_tip)
        tip_layout.setContentsMargins(15, 11, 15, 11)
        tip_layout.addWidget(styled_label("URUTAN FILE", "tipEyebrow"))
        tip_copy = styled_label("Untuk menggabungkan PDF, susun dokumen sebelum melanjutkan.", "tinyMuted")
        tip_copy.setWordWrap(True)
        tip_layout.addWidget(tip_copy)
        bottom.addWidget(privacy_tip, 2)
        layout.addLayout(bottom)
        self._refresh_activity()
        return page

    def _build_tools_page(self) -> QWidget:
        page = QWidget()
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 2, 0, 0)
        outer.setSpacing(5)
        outer.addWidget(styled_label("Semua alat", "pageTitle"))
        outer.addWidget(styled_label("Pilih operasi yang sesuai dengan dokumen Anda.", "mutedText"))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        contents = QWidget()
        contents.setObjectName("scrollContents")
        grid = QGridLayout(contents)
        grid.setContentsMargins(2, 12, 8, 12)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(11)
        for index, tool in enumerate(TOOLS):
            card = ToolCard(tool)
            card.tool_selected.connect(self._select_tool)
            grid.addWidget(card, index // 3, index % 3)
        scroll.setWidget(contents)
        outer.addWidget(scroll, 1)
        return page

    def _build_other_page(self) -> QWidget:
        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(0, 2, 0, 0)
        self.other_pages = QStackedWidget()
        self.history_page = HistoryPage()
        self.history_page.open_output.connect(self._open_output)
        self.history_page.open_folder.connect(self._open_folder)
        self.history_page.retry_job.connect(self._retry_from_history)
        self.history_page.clear_requested.connect(self._clear_history)
        self.other_pages.addWidget(self.history_page)
        self.history_page.set_entries(self._history_entries())
        self.other_pages.addWidget(self._build_settings_page())
        self.other_pages.addWidget(self._build_about_page())
        page_layout.addWidget(self.other_pages)
        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addWidget(styled_label("Pengaturan", "pageTitle"))
        layout.addWidget(styled_label("Atur lokasi penyimpanan dan kebutuhan konversi.", "mutedText"))
        surface = card_frame(object_name="surface")
        form = QFormLayout(surface)
        form.setContentsMargins(19, 18, 19, 18)
        form.setHorizontalSpacing(22)
        form.setVerticalSpacing(14)
        output_row = QHBoxLayout()
        self.default_output = QLineEdit(
            self.settings.value("output_directory", default_output_directory())
        )
        self.default_output.setObjectName("inputField")
        output_row.addWidget(self.default_output, 1)
        browse = QPushButton("Pilih folder")
        browse.setObjectName("secondaryButton")
        browse.clicked.connect(self._choose_default_output)
        output_row.addWidget(browse)
        output_widget = QWidget()
        output_widget.setLayout(output_row)
        form.addRow("Folder output default", output_widget)

        self.open_folder_setting = QCheckBox("Buka folder output setelah selesai")
        self.open_folder_setting.setChecked(self.settings.value("open_output", True, type=bool))
        form.addRow("Setelah proses", self.open_folder_setting)
        self.history_limit = QComboBox()
        self.history_limit.addItems(["20 proses", "50 proses", "100 proses"])
        index = min(max(int(self.settings.value("history_limit", 1)), 0), 2)
        self.history_limit.setCurrentIndex(index)
        form.addRow("Batas riwayat", self.history_limit)
        layout.addWidget(surface)
        dependency_card = card_frame(object_name="surface")
        dependency_layout = QVBoxLayout(dependency_card)
        dependency_layout.setContentsMargins(16, 13, 16, 13)
        dependency_layout.setSpacing(7)
        dependency_layout.addWidget(styled_label("Kebutuhan konversi Office", "sectionHeading"))
        dependency_layout.addWidget(
            styled_label(
                "Kebutuhan konversi Office diperiksa otomatis dan ditangani paket aplikasi.",
                "mutedText",
            )
        )
        dependency_row = QHBoxLayout()
        self.libreoffice_status = styled_label("Memeriksa komponen DocuConvert…", "statusText")
        self.libreoffice_status.setWordWrap(True)
        dependency_row.addWidget(self.libreoffice_status, 1)
        refresh_dependency = QPushButton("Periksa lagi")
        refresh_dependency.setObjectName("secondaryButton")
        refresh_dependency.clicked.connect(self._refresh_dependency_status)
        dependency_row.addWidget(refresh_dependency)
        dependency_layout.addLayout(dependency_row)
        dependency_help = QPushButton("Panduan DocuConvert")
        dependency_help.setObjectName("textButton")
        dependency_help.setAccessibleName("Buka panduan DocuConvert")
        dependency_help.clicked.connect(self._open_libreoffice_help)
        self.libreoffice_help_button = dependency_help
        dependency_layout.addWidget(dependency_help, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(dependency_card)
        self._refresh_dependency_status()
        actions = QHBoxLayout()
        actions.addStretch(1)
        save = QPushButton("Simpan pengaturan")
        save.setObjectName("primaryButton")
        save.clicked.connect(self._save_settings)
        actions.addWidget(save)
        layout.addLayout(actions)
        layout.addStretch(1)
        return page

    def _build_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(11)
        layout.addWidget(styled_label("Tentang DocuConvert", "pageTitle"))
        layout.addWidget(styled_label(f"Versi {VERSION}", "mutedText"))
        surface = card_frame(object_name="privacyCard")
        inner = QVBoxLayout(surface)
        inner.setContentsMargins(19, 18, 19, 18)
        inner.setSpacing(8)
        inner.addWidget(styled_label("Pengelola dokumen desktop", "sectionHeading"))
        copy = styled_label(
            "DocuConvert memproses dokumen secara lokal. File sumber dan hasil tetap berada "
            "di perangkat Anda.",
            "mutedText",
        )
        copy.setWordWrap(True)
        inner.addWidget(copy)
        layout.addWidget(surface)
        updates = card_frame(object_name="surface")
        update_layout = QVBoxLayout(updates)
        update_layout.setContentsMargins(19, 18, 19, 18)
        update_layout.addWidget(styled_label("Update aplikasi", "sectionHeading"))
        self.update_status = styled_label(
            "Update diperiksa otomatis saat aplikasi terhubung ke internet.", "mutedText"
        )
        self.update_status.setWordWrap(True)
        update_layout.addWidget(self.update_status)
        actions = QHBoxLayout()
        self.check_update_button = QPushButton("Cek update")
        self.check_update_button.setObjectName("secondaryButton")
        self.check_update_button.clicked.connect(lambda: self.updates.check(manual=True))
        actions.addWidget(self.check_update_button)
        self.install_update_button = QPushButton("Unduh update")
        self.install_update_button.setObjectName("primaryButton")
        self.install_update_button.clicked.connect(self._install_update)
        self.install_update_button.hide()
        actions.addWidget(self.install_update_button)
        actions.addStretch(1)
        update_layout.addLayout(actions)
        layout.addWidget(updates)
        layout.addStretch(1)
        return page

    def _choose_files(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Pilih dokumen",
            "",
            "Dokumen didukung (*.docx *.odt *.xlsx *.pptx *.pdf *.jpg *.jpeg *.png)",
        )
        self._add_files(paths)

    def _add_files(self, paths: list[str]) -> None:
        valid = [str(Path(path)) for path in paths if Path(path).is_file()]
        if valid:
            tool_name = self._guess_tool(valid)
            if len(valid) == 1 and Path(valid[0]).suffix.lower() == ".pdf":
                choices = [tool.name for tool in TOOLS if ".pdf" in tool.extensions]
                selected, accepted = QInputDialog.getItem(
                    self,
                    "Pilih pekerjaan PDF",
                    "Apa yang ingin Anda lakukan dengan file ini?",
                    choices,
                    choices.index(tool_name),
                    False,
                )
                if not accepted:
                    return
                tool_name = selected
            self._open_tool_dialog(tool_name, valid)

    def _select_tool(self, name: str) -> None:
        self._open_tool_dialog(name)

    def _open_tool_dialog(self, name: str, initial_files: list[str] | None = None) -> None:
        if self.job_page is not None:
            self.pages.removeWidget(self.job_page)
            self.job_page.deleteLater()
        self.return_page = self.pages.currentWidget()
        self.return_breadcrumb = self.breadcrumb.text()
        self.job_page = JobPanel(
            name,
            initial_files=initial_files,
            output_directory=self.settings.value(
                "output_directory", default_output_directory()
            ),
            open_output=self.settings.value("open_output", True, type=bool),
            libreoffice_path=self.libreoffice_path,
            parent=self.pages,
        )
        self.job_page.close_requested.connect(self._close_job_page)
        self.job_page.run_requested.connect(self._handle_job_request)
        self.job_page.cancel_requested.connect(self._cancel_job)
        self.job_page.job_state_changed.connect(self._update_job_status)
        self.job_page.open_output_requested.connect(self._open_output)
        self.job_page.open_folder_requested.connect(self._open_folder)
        self.job_page.dependency_help_requested.connect(self._open_libreoffice_help)
        self.pages.addWidget(self.job_page)
        self.pages.setCurrentWidget(self.job_page)
        self.breadcrumb.setText(f"DocuConvert   /   {name}")
        for button in self.nav_buttons.values():
            button.setChecked(False)
        count = len(self.job_page.files)
        self.status_label.setText(f"{count} file dipilih · {name}" if count else f"Pengaturan alat · {name}")

    def _close_job_page(self) -> None:
        if self.job_page is not None and self.pages.currentWidget() is self.job_page:
            target = self.return_page if self.return_page is not None else self.dashboard
            self.pages.setCurrentWidget(target)
        self.breadcrumb.setText(self.return_breadcrumb)
        page_name = self.return_breadcrumb.split("/")[-1].strip()
        for label, button in self.nav_buttons.items():
            button.setChecked(label == page_name)
        self.status_label.setText("Siap digunakan")

    def _update_job_status(self, status: str) -> None:
        if self.job_page is None:
            return
        self.status_label.setText(
            {
                "validating": f"Memeriksa · {self.job_page.tool.name}",
                "processing": f"Proses berjalan · {self.job_page.tool.name}",
                "unavailable": "Mesin pemrosesan belum tersedia",
                "completed": f"Selesai · {self.job_page.tool.name}",
                "failed": f"Proses gagal · {self.job_page.tool.name}",
                "cancelled": f"Proses dibatalkan · {self.job_page.tool.name}",
            }.get(status, "Siap digunakan")
        )

    @staticmethod
    def _guess_tool(paths: list[str]) -> str:
        extensions = {Path(path).suffix.lower() for path in paths}
        if len(paths) > 1 and extensions <= {".pdf"}:
            return TOOL_BY_KEY["merge_pdf"].name
        mapping = {
            ".docx": "word_to_pdf", ".odt": "word_to_pdf", ".xlsx": "excel_to_pdf",
            ".pptx": "powerpoint_to_pdf", ".jpg": "image_to_pdf",
            ".jpeg": "image_to_pdf", ".png": "image_to_pdf", ".pdf": "pdf_to_word",
        }
        return TOOL_BY_KEY[mapping.get(Path(paths[0]).suffix.lower(), "word_to_pdf")].name

    def _handle_job_request(self, _request: object) -> None:
        if self.job_page is None:
            return
        if self.job_page.tool.key in {"word_to_pdf", "excel_to_pdf", "powerpoint_to_pdf"}:
            if not self.libreoffice_path:
                self.job_page.set_unavailable(
                    "Komponen konversi DocuConvert belum tersedia. Periksa instalasi "
                    "atau gunakan paket lengkap DocuConvert. File Anda belum diproses."
                )
                return
        if self.job_controller is not None:
            job_id = self.job_controller.submit(_request)
            if job_id:
                self.job_page.backend_job_id = job_id
            return
        self.job_page.set_unavailable(
            "File dan pengaturan sudah diperiksa, tetapi mesin konversi belum tersedia. "
            "File sumber belum diubah."
        )

    def _cancel_job(self) -> None:
        if self.job_page is not None and self.job_page.backend_job_id and self.job_controller:
            self.job_page.request_cancellation()
            self.job_controller.cancel(self.job_page.backend_job_id)

    def _refresh_history(self) -> None:
        if hasattr(self, "history_page"):
            self.history_page.set_entries(self._history_entries())
            self._refresh_activity()

    def _history_entries(self) -> list[dict[str, object]]:
        if self.job_controller is None:
            return []
        return self.job_controller.history_entries(self._selected_history_limit())

    def _selected_history_limit(self) -> int:
        limits = (20, 50, 100)
        index = self.history_limit.currentIndex() if hasattr(self, "history_limit") else 2
        return limits[index]

    def _refresh_activity(self) -> None:
        if not hasattr(self, "activity_copy"):
            return
        entries = self._history_entries()
        if not entries:
            self.activity_copy.setText("Belum ada aktivitas. File Anda belum pernah diproses.")
            return
        latest = entries[0]
        status = {
            "completed": "Selesai",
            "failed": "Gagal",
            "cancelled": "Dibatalkan",
        }.get(str(latest.get("status")), "Diproses")
        sources = [Path(path).name for path in latest.get("sources", [])]
        file_text = ", ".join(sources[:2]) or "File tidak tersedia"
        self.activity_copy.setText(
            f"{status} · {latest.get('tool_name', 'Proses dokumen')} · {file_text}"
        )

    def _clear_history(self) -> None:
        answer = QMessageBox.question(
            self,
            "Hapus riwayat proses",
            "Hapus semua metadata riwayat dari perangkat ini? File hasil tidak akan dihapus.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            if self.job_controller:
                self.job_controller.clear_history()
            else:
                self._refresh_history()

    def _retry_from_history(self, tool_key: str, sources: object) -> None:
        if tool_key not in TOOL_BY_KEY or not isinstance(sources, list):
            return
        valid_sources = [str(path) for path in sources if Path(str(path)).is_file()]
        if not valid_sources:
            QMessageBox.information(
                self,
                "File sumber tidak ditemukan",
                "Pilih file sumber yang masih tersedia untuk mengatur ulang proses.",
            )
            return
        self._open_tool_dialog(TOOL_BY_KEY[tool_key].name, valid_sources)

    def _handle_backend_event(self, event: object) -> None:
        if self.job_page is None or self.job_page.backend_job_id != getattr(event, "job_id", None):
            return
        status = getattr(getattr(event, "status", None), "value", "")
        if status == "queued":
            self.job_page.set_validating()
        elif status == "running":
            self.job_page.set_processing(
                int(getattr(event, "progress", 0)), str(getattr(event, "message", ""))
            )
        elif status == "completed":
            self.job_page.set_completed(
                [str(path) for path in getattr(event, "output_files", ())],
                warnings=list(getattr(event, "warnings", ())),
            )
        elif status == "failed":
            self.job_page.set_failed(
                str(getattr(event, "error_message", "") or "Proses gagal."),
                recovery=str(
                    getattr(event, "error_recovery", None)
                    or "Periksa file dan pengaturan, lalu coba lagi."
                ),
            )
        elif status == "cancelled":
            self.job_page.set_cancelled(str(getattr(event, "message", "Proses dibatalkan.")))

    def _handle_submission_failure(self, message: str, recovery: str) -> None:
        if self.job_page is not None:
            self.job_page.set_failed(message, recovery=recovery)

    def _open_output(self, output_path: str) -> None:
        path = Path(output_path)
        if not path.is_file():
            QMessageBox.information(
                self,
                "File hasil tidak ditemukan",
                "File mungkin sudah dipindahkan atau dihapus. Anda dapat mengatur ulang proses dari riwayat.",
            )
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
            QMessageBox.information(self, "Tidak dapat membuka file", "Periksa aplikasi default untuk format file ini.")

    def _open_folder(self, folder_path: str) -> None:
        path = Path(folder_path)
        if not path.is_dir():
            QMessageBox.information(self, "Folder tidak ditemukan", "Folder hasil sudah dipindahkan atau dihapus.")
            return
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(path))):
            QMessageBox.information(self, "Tidak dapat membuka folder", "Buka folder output melalui File Explorer.")

    def _refresh_dependency_status(self) -> None:
        preferred_path = self.settings.value("libreoffice_executable") or None
        self.libreoffice_path = find_libreoffice(preferred_path)
        if self.job_controller is not None:
            self.job_controller.runtime.conversions.set_libreoffice_executable(
                self.libreoffice_path
            )
        if not hasattr(self, "libreoffice_status"):
            return
        if self.libreoffice_path:
            self.libreoffice_status.setObjectName("statusSuccess")
            self.libreoffice_status.setText("DocuConvert siap mengonversi dokumen Office.")
            self.libreoffice_help_button.hide()
        else:
            self.libreoffice_status.setObjectName("statusWarning")
            self.libreoffice_status.setText(
                "Komponen konversi DocuConvert belum tersedia. "
                "Periksa instalasi atau gunakan paket lengkap DocuConvert."
            )
            self.libreoffice_help_button.show()
        self._repolish(self.libreoffice_status)

    @staticmethod
    def _repolish(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    @staticmethod
    def _open_libreoffice_help() -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/AgungCandraS/DokuConvert#pasang-dan-mulai-gunakan"))

    def _choose_default_output(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Pilih folder output", self.default_output.text()
        )
        if path:
            self.default_output.setText(path)

    def _save_settings(self) -> None:
        self.settings.setValue("output_directory", self.default_output.text().strip())
        self.settings.setValue("open_output", self.open_folder_setting.isChecked())
        self.settings.setValue("history_limit", self.history_limit.currentIndex())
        if self.job_controller is not None:
            self.job_controller.runtime.history.limit = self._selected_history_limit()
        self.status_label.setText("Pengaturan disimpan")

    def _navigate(self, page: str) -> None:
        self.breadcrumb.setText(f"DocuConvert   /   {page}")
        if page == "Beranda":
            self.pages.setCurrentWidget(self.dashboard)
        elif page == "Semua alat":
            self.pages.setCurrentWidget(self.tools_page)
        else:
            self.pages.setCurrentWidget(self.other_page)
            self.other_pages.setCurrentIndex({"Riwayat": 0, "Pengaturan": 1, "Tentang": 2}.get(page, 0))
        for label, button in self.nav_buttons.items():
            button.setChecked(label == page)

    def _toggle_theme(self) -> None:
        self.dark_mode = not self.dark_mode
        self.settings.setValue("theme", "dark" if self.dark_mode else "light")
        self._apply_theme()

    def _apply_theme(self) -> None:
        app = QApplication.instance()
        if app is not None:
            palette = QPalette()
            colors = (
                ("#202722", "#e3e9e4", "#252e28", "#3b5941", "#ffffff")
                if self.dark_mode else
                ("#f3f4f1", "#26332c", "#ffffff", "#dce8dc", "#26332c")
            )
            for role, color in (
                (QPalette.ColorRole.Window, colors[0]),
                (QPalette.ColorRole.WindowText, colors[1]),
                (QPalette.ColorRole.Text, colors[1]),
                (QPalette.ColorRole.ButtonText, colors[1]),
                (QPalette.ColorRole.Base, colors[2]),
                (QPalette.ColorRole.Button, colors[2]),
                (QPalette.ColorRole.Highlight, colors[3]),
                (QPalette.ColorRole.HighlightedText, colors[4]),
            ):
                palette.setColor(role, QColor(color))
            app.setPalette(palette)
            stylesheet = DARK_STYLESHEET if self.dark_mode else LIGHT_STYLESHEET
            app.setStyleSheet(
                stylesheet.replace("__LIGHT_ARROW__", icon_path("chevron-light.svg").as_posix())
                .replace("__DARK_ARROW__", icon_path("chevron-dark.svg").as_posix())
            )

    def _update_checked(self, release: object, manual: bool) -> None:
        if not isinstance(release, UpdateRelease):
            self.update_status.setText("Aplikasi sudah menggunakan versi terbaru yang tersedia.")
            return
        if self.available_update is None or self.available_update.version != release.version:
            self.update_package = None
            self.install_update_button.setText("Unduh update")
        self.available_update = release
        self.install_update_button.show()
        self.update_status.setText(f"Update versi {release.version} tersedia.")
        if manual or self._notified_version != release.version:
            self._notified_version = release.version
            notice = QMessageBox(self)
            notice.setWindowTitle("Update DocuConvert tersedia")
            notice.setText(
                f"Versi {release.version} tersedia. "
                "Buka Tentang untuk mengunduh dan memasang update."
            )
            notice.setStandardButtons(QMessageBox.StandardButton.Ok)
            notice.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
            notice.open()

    def _update_busy(self, busy: bool) -> None:
        self.check_update_button.setEnabled(not busy)
        self.install_update_button.setEnabled(not busy)

    def _update_progress(self, percent: int) -> None:
        self.update_status.setText(f"Mengunduh update: {percent}%")

    def _update_failed(self, message: str, manual: bool) -> None:
        self.update_status.setText(
            "Belum dapat memeriksa atau mengunduh update. Akan dicoba lagi otomatis."
        )
        if manual:
            QMessageBox.warning(self, "Update belum berhasil", message)

    def _update_downloaded(self, package: object) -> None:
        if isinstance(package, Path):
            self.update_package = package
            self.install_update_button.setText("Pasang update dan mulai ulang")
            self.update_status.setText("Update sudah diunduh dan diverifikasi. Siap dipasang.")

    def _install_update(self) -> None:
        if self.update_package is None:
            if self.available_update is not None:
                self.update_status.setText("Memulai unduhan update…")
                self.updates.download(self.available_update)
            return
        if self.job_controller and any(
            job.status in {JobStatus.QUEUED, JobStatus.RUNNING}
            for job in self.job_controller.runtime.jobs.jobs()
        ):
            QMessageBox.information(
                self, "Proses masih berjalan", "Tunggu konversi selesai sebelum memasang update."
            )
            return
        answer = QMessageBox.question(
            self, "Pasang update",
            "Pasang update sekarang? Aplikasi akan ditutup untuk memperbarui versi.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            if launch_update(self.update_package):
                QApplication.instance().quit()
        except (OSError, ValueError) as exc:
            QMessageBox.warning(self, "Update belum berhasil", str(exc))
