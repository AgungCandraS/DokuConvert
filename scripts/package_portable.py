"""Create and verify a lossless Windows-compatible ZIP of a complete portable build."""

from __future__ import annotations

import argparse
import hashlib
import os
import tempfile
import time
import zipfile
from pathlib import Path


def package_portable(source: Path, destination: Path) -> tuple[int, int]:
    source = source.resolve(strict=True)
    destination = destination.resolve()
    if not source.is_dir() or not (source / "DocuConvert" / "DocuConvert.exe").is_file():
        raise ValueError("Pilih folder hasil build yang berisi DocuConvert/DocuConvert.exe.")
    if destination.exists():
        raise FileExistsError(f"Paket sudah ada: {destination}")
    if source == destination or source in destination.parents:
        raise ValueError("Simpan ZIP di luar folder sumber agar tidak ikut dipaketkan.")
    checksum_path = destination.with_suffix(destination.suffix + ".sha256")
    if checksum_path.exists():
        raise FileExistsError(f"Checksum sudah ada: {checksum_path}")
    files = sorted(path for path in source.rglob("*") if path.is_file())
    for path in files:
        if path.is_symlink() or not path.resolve().is_relative_to(source):
            raise ValueError(f"File di luar folder build tidak dapat dipaketkan: {path}")
    original_size = sum(path.stat().st_size for path in files)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=".docuconvert-", suffix=".zip.part", dir=destination.parent
    )
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True
        ) as archive:
            processed = 0
            last_report = time.monotonic()
            for path in files:
                archive.write(path, path.relative_to(source).as_posix())
                processed += path.stat().st_size
                if time.monotonic() - last_report >= 15:
                    percent = processed * 100 / max(original_size, 1)
                    print(
                        f"Mengompres paket DocuConvert: {percent:.0f}%",
                        flush=True,
                    )
                    last_report = time.monotonic()
        print("Memverifikasi seluruh file paket DocuConvert...", flush=True)
        with zipfile.ZipFile(temporary) as archive:
            corrupt = archive.testzip()
            if corrupt:
                raise ValueError(f"Verifikasi paket gagal: {corrupt}")
            if archive.namelist() != [path.relative_to(source).as_posix() for path in files]:
                raise ValueError("Daftar file paket tidak sesuai folder sumber.")
        with temporary.open("rb") as package:
            digest = hashlib.file_digest(package, "sha256").hexdigest()
        # Publish exclusively so a concurrent build cannot overwrite an existing package.
        os.link(temporary, destination)
        with checksum_path.open("x", encoding="ascii") as checksum:
            checksum.write(f"{digest}  {destination.name}\n")
        return original_size, destination.stat().st_size
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    original, compressed = package_portable(args.source, args.destination)
    reduction = (1 - compressed / max(original, 1)) * 100
    print(
        f"Paket DocuConvert: {original / 1024**2:.1f} MiB menjadi {compressed / 1024**2:.1f} MiB "
        f"({reduction:.1f}% lebih kecil).",
        flush=True,
    )
    print(f"ZIP siap digunakan: {args.destination.resolve()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
