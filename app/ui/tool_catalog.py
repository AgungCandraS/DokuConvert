"""Single source of truth for tool labels, input types, and setup guidance."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    key: str
    name: str
    input_formats: str
    description: str
    guidance: str
    icon: str
    accent: str
    extensions: frozenset[str]
    multiple_files: bool = False
    ordered_files: bool = False


TOOLS = (
    ToolDefinition(
        "word_to_pdf", "Word ke PDF", "DOCX → PDF", "Ubah dokumen Word menjadi PDF",
        "Setiap dokumen akan menjadi satu file PDF dengan nama yang sama.", "word.svg", "#2866b4",
        frozenset({".docx", ".odt"}), True,
    ),
    ToolDefinition(
        "excel_to_pdf", "Excel ke PDF", "XLSX", "Simpan spreadsheet sebagai PDF",
        "Spreadsheet diekspor sebagai PDF. Pengaturan halaman dari dokumen akan dipertahankan.",
        "excel.svg", "#147345", frozenset({".xlsx"}), True,
    ),
    ToolDefinition(
        "powerpoint_to_pdf", "PowerPoint ke PDF", "PPTX", "Ubah presentasi menjadi PDF",
        "Setiap presentasi akan diekspor sebagai satu file PDF.", "powerpoint.svg", "#c44f31",
        frozenset({".pptx"}), True,
    ),
    ToolDefinition(
        "pdf_to_word", "PDF ke Word", "PDF → DOCX", "Jadikan PDF dapat diedit",
        "PDF berbasis teks memberi hasil terbaik. Tata letak kompleks atau hasil scan dapat berubah.",
        "pdf.svg", "#b94f3b", frozenset({".pdf"}),
    ),
    ToolDefinition(
        "merge_pdf", "Gabungkan PDF", "PDF + PDF", "Satukan beberapa PDF",
        "Tambahkan minimal dua PDF, lalu atur urutannya sebelum digabung.", "merge.svg", "#79866b",
        frozenset({".pdf"}), True, True,
    ),
    ToolDefinition(
        "split_pdf", "Pisahkan PDF", "HALAMAN", "Ambil atau pisahkan halaman",
        "Tentukan halaman yang ingin diambil. Gunakan koma untuk memilih beberapa halaman atau rentang.",
        "split.svg", "#b97557", frozenset({".pdf"}),
    ),
    ToolDefinition(
        "compress_pdf", "Kompres PDF", "PDF", "Kurangi ukuran file PDF",
        "Pilih keseimbangan antara ukuran file dan kualitas visual.", "compress.svg", "#7a8870",
        frozenset({".pdf"}),
    ),
    ToolDefinition(
        "image_to_pdf", "Gambar ke PDF", "JPG · PNG", "Satukan gambar dalam PDF",
        "Setiap gambar menjadi satu halaman. Urutan daftar menentukan urutan halaman.", "image.svg",
        "#b98955", frozenset({".jpg", ".jpeg", ".png"}), True, True,
    ),
    ToolDefinition(
        "pdf_to_image", "PDF ke Gambar", "PDF → PNG", "Ekspor halaman sebagai gambar",
        "Ekspor satu gambar untuk setiap halaman, dengan format dan resolusi yang Anda pilih.",
        "pdf-image.svg", "#a8634d", frozenset({".pdf"}),
    ),
    ToolDefinition(
        "rotate_pdf", "Putar Halaman PDF", "PDF", "Perbaiki orientasi halaman",
        "Pilih halaman dan arah putaran. Halaman lain akan tetap seperti semula.", "pdf.svg", "#667b82",
        frozenset({".pdf"}),
    ),
    ToolDefinition(
        "delete_pages", "Hapus Halaman PDF", "PDF", "Buang halaman yang tidak diperlukan",
        "Tentukan halaman yang akan dihapus. Halaman yang tersisa disimpan sebagai PDF baru.",
        "split.svg", "#9a6659", frozenset({".pdf"}),
    ),
    ToolDefinition(
        "watermark_pdf", "Watermark PDF", "PDF", "Tambahkan penanda teks pada dokumen",
        "Atur teks watermark, posisi, dan tingkat transparansi sebelum menyimpan salinan baru.",
        "pdf.svg", "#7b7790", frozenset({".pdf"}),
    ),
    ToolDefinition(
        "protect_pdf", "Lindungi PDF", "PDF", "Beri password pada dokumen",
        "Buat password untuk membatasi pembukaan dokumen. Simpan password di tempat aman.",
        "pdf.svg", "#89734e", frozenset({".pdf"}),
    ),
)

TOOL_BY_NAME = {tool.name: tool for tool in TOOLS}
TOOL_BY_KEY = {tool.key: tool for tool in TOOLS}
FEATURED_TOOL_KEYS = (
    "word_to_pdf", "merge_pdf", "compress_pdf", "image_to_pdf", "pdf_to_word", "pdf_to_image"
)
