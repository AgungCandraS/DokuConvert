"""Trim a bundled LibreOffice to the files needed for headless Office-to-PDF conversion.

Hanya menghapus data yang tidak dipakai `soffice --headless --convert-to pdf`:
- share/extensions/dict-*: kamus spellcheck/thesaurus (ratusan MB).
- help, readmes: konten bantuan.
- share/gallery, share/template, share/wizards, share/autotext, share/autocorr:
  konten editor, bukan mesin konversi.
- share/config/images_*: tema ikon UI selain Colibre (default); headless tidak memuat ikon.
- share/xpdfimport: filter impor PDF ke Draw (operasi PDF memakai PyMuPDF).
- program/resource/*: bahasa selain `common`, `id`, dan `en*` (fallback bahasa Inggris
  sudah tertanam di binary; konversi tidak menampilkan dialog).

Sengaja TIDAK dihapus: program/*.dll, registry, Fonts, dan program/python-core
(bridge filter berisiko jika dihapus; penghematannya kecil dibanding risikonya).

Dapat dipakai lintas platform (layout Windows maupun LibreOffice.app di macOS)
karena pencocokan memakai pola path relatif, bukan lokasi absolut.
"""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

# Direktori berdasarkan nama (tahan terhadap perbedaan layout Windows vs macOS).
_PRUNE_DIR_NAMES = {
    "help",
    "readmes",
    "gallery",
    "template",
    "wizards",
    "autotext",
    "autocorr",
    "xpdfimport",
}

# Pola file zip tema ikon yang dihapus; tema Colibre (default) dipertahankan.
_ICON_THEME_KEEP = ("images_colibre.zip", "images_colibre_svg.zip")

# Bahasa resource yang dipertahankan; sisanya dihapus.
_RESOURCE_KEEP = {"common", "id"}

_SOFFICE_NAMES = {"soffice.exe", "soffice.com", "soffice"}


def _find_soffice(root: Path) -> Path | None:
    for path in root.rglob("*"):
        if path.is_file() and path.name in _SOFFICE_NAMES:
            # Hindari folder python-core milik LibreOffice yang juga membawa python.exe,
            # tetapi soffice tidak pernah bernama python; pencocokan nama sudah cukup.
            if "program" in path.relative_to(root).parts or root.name.endswith(".app"):
                return path
    return None


def _collect_targets(root: Path) -> list[Path]:
    targets: list[Path] = []
    for path in root.rglob("*"):
        parts = path.relative_to(root).parts
        if path.is_dir():
            if path.name in {"help", "readmes"} and len(parts) <= 2:
                targets.append(path)
            elif "share" in parts and path.name in _PRUNE_DIR_NAMES:
                targets.append(path)
            elif "extensions" in parts and path.name.startswith("dict-"):
                targets.append(path)
            elif len(parts) >= 2 and parts[-2] == "resource" and "program" in parts:
                if path.name not in _RESOURCE_KEEP and not path.name.startswith("en"):
                    targets.append(path)
        elif path.is_file():
            if (
                "config" in parts
                and path.name.startswith("images_")
                and path.name.endswith(".zip")
                and path.name not in _ICON_THEME_KEEP
            ):
                targets.append(path)
    # Hapus duplikat/bersarang: jika induk sudah ditarget, anak tidak perlu.
    targets.sort(key=lambda p: len(p.parts))
    pruned: list[Path] = []
    for target in targets:
        if not any(target == other or target.is_relative_to(other) for other in pruned):
            pruned.append(target)
    return pruned


def _size_of(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(child.stat().st_size for child in path.rglob("*") if child.is_file())


def prune_libreoffice(root: Path | str, dry_run: bool = False) -> tuple[int, int]:
    """Pangkas distribusi LibreOffice. Mengembalikan (jumlah_target, byte_dibebaskan)."""
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"Folder LibreOffice tidak ditemukan: {root}")
    if _find_soffice(root) is None:
        raise ValueError(f"Bukan distribusi LibreOffice (soffice tidak ditemukan): {root}")
    targets = _collect_targets(root)
    reclaimed = sum(_size_of(target) for target in targets if target.exists())
    if not dry_run:
        for target in targets:
            if not target.exists():
                continue
            if target.is_dir() and not target.is_symlink():
                shutil.rmtree(target, ignore_errors=False)
            else:
                target.unlink()
        if _find_soffice(root) is None:
            raise RuntimeError("Pruning merusak distribusi LibreOffice; soffice hilang.")
    return len(targets), reclaimed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("libreoffice", type=Path, help="Folder LibreOffice yang dibundel.")
    parser.add_argument("--dry-run", action="store_true", help="Hanya laporkan tanpa menghapus.")
    args = parser.parse_args()
    count, reclaimed = prune_libreoffice(args.libreoffice, dry_run=args.dry_run)
    mode = "akan dibebaskan" if args.dry_run else "dibebaskan"
    print(f"LibreOffice diet: {count} target, {reclaimed / 1024**2:.1f} MiB {mode}.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
