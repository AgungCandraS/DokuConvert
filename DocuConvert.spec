# PyInstaller one-folder build shared by the native per-OS release jobs.
import sys
import os
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH).resolve()
with (project_root / "pyproject.toml").open("rb") as project_file:
    default_version = tomllib.load(project_file)["project"]["version"]
build_version = os.environ.get("DOCUCONVERT_BUILD_VERSION", default_version)
version_stamp = project_root / "build" / "release-version" / "VERSION"
version_stamp.parent.mkdir(parents=True, exist_ok=True)
version_stamp.write_text(build_version, encoding="utf-8")
pdf2docx_datas, pdf2docx_binaries, pdf2docx_hiddenimports = collect_all("pdf2docx")
pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all("pymupdf")

# Diet bundle: drop heavy files yang tidak dipakai fitur aplikasi.
# - opencv_videoio_ffmpeg: codec video, pdf2docx hanya pakai pemrosesan gambar.
# - Qt6Quick/Qml/Pdf/VirtualKeyboard: aplikasi hanya pakai QtCore/QtGui/QtWidgets
#   (terverifikasi via grep, tidak ada import QtQuick/Qml/QtPdf).
# - PIL _avif/_heic: hanya JPG/PNG yang didukung (lihat PRD FR-006).
# - pymupdf *.lib: static lib, tidak dibutuhkan saat runtime.
# - tcl/tk: aplikasi memakai PySide6, bukan tkinter.
_DROPPED_BINARY_SUBSTRINGS = (
    "opencv_videoio_ffmpeg",
    "qt6quick",
    "qt6qml",
    "qt6pdf",
    "qt6virtualkeyboard",
    "qt6quick3d",
    "qt6charts",
    "qt6datavisualization",
    "_avif",
    "_heic",
)
_DROPPED_DATA_SUBSTRINGS = (
    "mupdf-devel",
    "mupdfcpp64.lib",
    "_tcl_data",
    "_tk_data",
    "tcl8",
    "tk8",
)


def _keep_binary(entry):
    dest = entry[0].replace("\\", "/").lower()
    return not any(marker in dest for marker in _DROPPED_BINARY_SUBSTRINGS)


def _keep_data(entry):
    dest = entry[0].replace("\\", "/").lower()
    return not any(marker in dest for marker in _DROPPED_DATA_SUBSTRINGS)


pdf2docx_binaries = [entry for entry in pdf2docx_binaries if _keep_binary(entry)]
pymupdf_binaries = [entry for entry in pymupdf_binaries if _keep_binary(entry)]
pdf2docx_datas = [entry for entry in pdf2docx_datas if _keep_data(entry)]
pymupdf_datas = [entry for entry in pymupdf_datas if _keep_data(entry)]

a = Analysis(
    [str(project_root / "app" / "main.py")],
    pathex=[str(project_root)],
    binaries=pdf2docx_binaries + pymupdf_binaries,
    datas=[
        (str(version_stamp), "app"),
        (str(project_root / "app" / "ui" / "resources" / "icons"), "app/ui/resources/icons"),
        *pdf2docx_datas,
        *pymupdf_datas,
    ],
    hiddenimports=pdf2docx_hiddenimports + pymupdf_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "_tkinter",
        "tcl",
        "tk",
        "Tkinter",
        "FixTk",
        "PySide6.QtQuick",
        "PySide6.QtQml",
        "PySide6.QtPdf",
    ],
    noarchive=False,
    optimize=1,
)
# Qt DLLs (Qt6Quick/Qml/Pdf/...) dikumpulkan oleh hook bawaan PyInstaller,
# bukan via collect_all di atas, jadi saring hasil akhir Analysis juga.
a.binaries = [entry for entry in a.binaries if _keep_binary(entry)]
a.datas = [entry for entry in a.datas if _keep_data(entry)]
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="DocuConvert",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=(
        str(project_root / "app" / "ui" / "resources" / "icons" / "app-icon.ico")
        if sys.platform == "win32"
        else None
    ),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="DocuConvert",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="DocuConvert.app",
        bundle_identifier="com.docuconvert.desktop",
        info_plist={
            "CFBundleName": "DocuConvert",
            "CFBundleDisplayName": "DocuConvert",
            "CFBundleShortVersionString": build_version,
            "NSHighResolutionCapable": True,
        },
    )
