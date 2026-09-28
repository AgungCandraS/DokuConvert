"""Operation-specific form controls for document tools."""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QLabel, QLineEdit, QWidget

from app.ui.tool_catalog import ToolDefinition


class ToolOptions(QWidget):
    """Build and expose only the settings relevant to a selected tool."""

    def __init__(self, tool: ToolDefinition, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fields: dict[str, QWidget] = {}
        self.password_confirm: QLineEdit | None = None
        self.form = QFormLayout(self)
        self.form.setContentsMargins(0, 0, 0, 0)
        self.form.setHorizontalSpacing(22)
        self.form.setVerticalSpacing(10)
        self._build(tool)

    def _line(self, name: str, label: str, value: str = "", hint: str = "") -> QLineEdit:
        field = QLineEdit(value)
        field.setObjectName("inputField")
        field.setPlaceholderText(hint)
        self.fields[name] = field
        self.form.addRow(label, field)
        return field

    def _combo(
        self, name: str, label: str, choices: list[tuple[str, object]], default: int = 0
    ) -> QComboBox:
        field = QComboBox()
        for title, value in choices:
            field.addItem(title, value)
        field.setCurrentIndex(default)
        self.fields[name] = field
        self.form.addRow(label, field)
        return field

    def _check(
        self, name: str | None, label: str, text: str, checked: bool = False
    ) -> QCheckBox:
        field = QCheckBox(text)
        field.setChecked(checked)
        if name:
            self.fields[name] = field
        self.form.addRow(label, field)
        return field

    def _note(self, text: str, *, warning: bool = False) -> None:
        note = QLabel(text)
        note.setObjectName("warningText" if warning else "tinyMuted")
        note.setWordWrap(True)
        self.form.addRow("Catatan" if warning else "", note)

    def _build(self, tool: ToolDefinition) -> None:
        key = tool.key
        if key == "split_pdf":
            self._combo(
                "split_mode", "Cara memisahkan",
                [("Ekstrak halaman ke satu PDF", "extract"),
                 ("Simpan setiap rentang sebagai PDF", "ranges")],
            )
            self._line("page_ranges", "Halaman", "1-3", "Contoh: 1-3,5,8-10")
            self._note("Gunakan nomor halaman mulai dari 1.")
        elif key == "compress_pdf":
            self._combo(
                "quality", "Kualitas",
                [("Seimbang · rekomendasi", "balanced"),
                 ("Ukuran lebih kecil · kualitas lebih rendah", "small"),
                 ("Kualitas lebih tinggi · ukuran lebih besar", "quality")],
            )
            self._note("Hasil sebaiknya dibandingkan dengan ukuran file sumber.")
        elif key == "pdf_to_image":
            self._combo(
                "image_format", "Format gambar",
                [("PNG · lebih tajam", "png"), ("JPG · ukuran lebih kecil", "jpg")],
            )
            self._combo(
                "resolution", "Resolusi",
                [("Ringan · 96 DPI", 96), ("Standar · 150 DPI", 150), ("Tinggi · 300 DPI", 300)],
                default=1,
            )
            self._line("image_page_range", "Halaman tertentu", hint="Kosongkan untuk semua halaman")
        elif key == "image_to_pdf":
            self._combo(
                "page_size", "Ukuran halaman",
                [("A4", "A4"), ("Letter", "Letter"), ("Ukuran gambar asli", "image")],
            )
            self._combo(
                "orientation", "Orientasi",
                [("Otomatis mengikuti gambar", "auto"), ("Potret", "portrait"), ("Lanskap", "landscape")],
            )
            self._check("fit_to_page", "Tata letak", "Sesuaikan gambar agar pas di halaman", True)
        elif key == "pdf_to_word":
            self._note(
                "PDF hasil scan memerlukan OCR. Tabel, kolom, dan font khusus mungkin berubah.",
                warning=True,
            )
        elif key in {"rotate_pdf", "delete_pages"}:
            self._line("page_ranges", "Halaman", "1", "Contoh: 1-3,5")
            if key == "rotate_pdf":
                self._combo(
                    "rotation", "Putar",
                    [("90° searah jarum jam", 90), ("180°", 180),
                     ("90° berlawanan arah jarum jam", 270)],
                )
            else:
                self._note("Halaman yang disebutkan akan dihapus dari salinan hasil.")
        elif key == "watermark_pdf":
            self._line("watermark_text", "Teks watermark", hint="Contoh: DOKUMEN INTERNAL")
            self._combo(
                "watermark_position", "Posisi",
                [("Tengah", "center"), ("Diagonal", "diagonal"), ("Bagian bawah", "bottom")],
            )
            self._combo(
                "watermark_opacity", "Transparansi",
                [("Tipis", "light"), ("Sedang", "medium"), ("Jelas", "strong")],
                default=1,
            )
        elif key == "protect_pdf":
            password = self._line("password", "Password", hint="Masukkan password")
            password.setEchoMode(QLineEdit.EchoMode.Password)
            confirmation = self._line("password_confirm", "Konfirmasi", hint="Ulangi password")
            confirmation.setEchoMode(QLineEdit.EchoMode.Password)
            self.password_confirm = confirmation
            self.fields.pop("password_confirm")
            reveal = self._check(None, "", "Tampilkan password")
            reveal.toggled.connect(lambda visible: self._toggle_password(visible, password, confirmation))
            self._note("Simpan password di tempat aman. Password tidak dapat dipulihkan.", warning=True)

    @staticmethod
    def _toggle_password(visible: bool, password: QLineEdit, confirmation: QLineEdit) -> None:
        mode = QLineEdit.EchoMode.Normal if visible else QLineEdit.EchoMode.Password
        password.setEchoMode(mode)
        confirmation.setEchoMode(mode)

    def request_values(self) -> dict[str, object]:
        values: dict[str, object] = {}
        for name, field in self.fields.items():
            if isinstance(field, QLineEdit):
                values[name] = field.text().strip()
            elif isinstance(field, QComboBox):
                values[name] = field.currentData()
            elif isinstance(field, QCheckBox):
                values[name] = field.isChecked()
        return values
