"""Build a macOS installer package containing DocuConvert and LibreOffice."""

from __future__ import annotations

import argparse
import hashlib
import platform
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--libreoffice-app", type=Path, required=True)
    parser.add_argument("--version")
    parser.add_argument("--output-directory", type=Path)
    args = parser.parse_args()

    if sys.platform != "darwin":
        parser.error("Paket macOS harus dibuat di macOS.")

    project_root = Path(__file__).resolve().parents[1]
    with (project_root / "pyproject.toml").open("rb") as project_file:
        project_version = tomllib.load(project_file)["project"]["version"]
    version = args.version or project_version
    libreoffice_app = args.libreoffice_app.expanduser().resolve()
    soffice = libreoffice_app / "Contents" / "MacOS" / "soffice"
    if not soffice.is_file():
        parser.error(f"LibreOffice.app tidak lengkap atau soffice tidak ditemukan: {soffice}")

    architecture = platform.machine().lower()
    output_directory = args.output_directory or (
        project_root / "dist" / f"release-macos-{architecture}-{version}"
    )
    output_directory = output_directory.resolve()
    if output_directory.exists():
        parser.error(f"Folder output sudah ada; pilih folder baru agar hasil tidak tertimpa: {output_directory}")
    output_directory.mkdir(parents=True)

    with tempfile.TemporaryDirectory(prefix="docuconvert-macos-build-") as temp_name:
        temp_root = Path(temp_name)
        temp_dist = temp_root / "dist"
        temp_work = temp_root / "work"
        subprocess.run(
            [
                sys.executable,
                "-m",
                "PyInstaller",
                "--clean",
                "--noconfirm",
                "--distpath",
                str(temp_dist),
                "--workpath",
                str(temp_work),
                str(project_root / "DocuConvert.spec"),
            ],
            cwd=project_root,
            check=True,
        )

        app_bundle = temp_dist / "DocuConvert.app"
        if not app_bundle.is_dir():
            raise RuntimeError(f"PyInstaller tidak menghasilkan app bundle: {app_bundle}")
        resources = app_bundle / "Contents" / "Resources"
        bundled_libreoffice = resources / "tools" / "libreoffice" / "LibreOffice.app"
        bundled_libreoffice.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(libreoffice_app, bundled_libreoffice, symlinks=True)
        shutil.copy2(
            project_root / "THIRD_PARTY_NOTICES.md",
            resources / "THIRD_PARTY_NOTICES.md",
        )
        shutil.copy2(project_root / "LICENSE", resources / "LICENSE")

        package_root = temp_root / "package-root"
        install_app = package_root / "Applications" / "DocuConvert.app"
        install_app.parent.mkdir(parents=True)
        shutil.copytree(app_bundle, install_app, symlinks=True)

        package_name = f"DocuConvert-{version}-macos-{architecture}.pkg"
        package_path = output_directory / package_name
        command = [
            "pkgbuild",
            "--root",
            str(package_root),
            "--identifier",
            "com.docuconvert.desktop",
            "--version",
            version,
            "--install-location",
            "/",
        ]
        command.append(str(package_path))
        subprocess.run(command, check=True)

    checksum = hashlib.sha256(package_path.read_bytes()).hexdigest()
    (output_directory / "SHA256SUMS.txt").write_text(
        f"{checksum}  {package_name}\n", encoding="ascii"
    )
    print(f"Installer macOS berhasil dibuat: {package_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
