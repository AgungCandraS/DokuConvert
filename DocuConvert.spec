# PyInstaller one-folder build shared by the native per-OS release jobs.
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all


project_root = Path(SPECPATH).resolve()
pdf2docx_datas, pdf2docx_binaries, pdf2docx_hiddenimports = collect_all("pdf2docx")
pymupdf_datas, pymupdf_binaries, pymupdf_hiddenimports = collect_all("pymupdf")

a = Analysis(
    [str(project_root / "app" / "main.py")],
    pathex=[str(project_root)],
    binaries=pdf2docx_binaries + pymupdf_binaries,
    datas=[
        (str(project_root / "app" / "ui" / "resources" / "icons"), "app/ui/resources/icons"),
        *pdf2docx_datas,
        *pymupdf_datas,
    ],
    hiddenimports=pdf2docx_hiddenimports + pymupdf_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
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
            "CFBundleShortVersionString": "0.1.0",
            "NSHighResolutionCapable": True,
        },
    )
