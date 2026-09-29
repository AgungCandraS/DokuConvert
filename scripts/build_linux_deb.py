"""Build a Debian/Ubuntu installer package from the PyInstaller application."""

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


RUNTIME_DEPENDENCIES = (
    "libc6 (>= 2.35), libgcc-s1, libstdc++6, libgl1, libegl1, libglib2.0-0, "
    "libx11-6, libx11-xcb1, libxcb1, libxcb-cursor0, libxcb-icccm4, "
    "libxcb-image0, libxcb-keysyms1, libxcb-randr0, libxcb-render-util0, "
    "libxcb-shape0, libxcb-shm0, libxcb-sync1, libxcb-xfixes0, libxcb-xinerama0, "
    "libxcb-xkb1, libxkbcommon0, libxkbcommon-x11-0, libreoffice"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version")
    parser.add_argument("--output-directory", type=Path)
    args = parser.parse_args()

    if not sys.platform.startswith("linux"):
        parser.error("Paket Linux harus dibuat di Linux.")
    if platform.machine().lower() not in {"x86_64", "amd64"}:
        parser.error("Build Linux saat ini hanya mendukung arsitektur x86_64/amd64.")
    if not shutil.which("dpkg-deb"):
        parser.error("dpkg-deb tidak ditemukan; jalankan build pada Debian/Ubuntu.")

    project_root = Path(__file__).resolve().parents[1]
    with (project_root / "pyproject.toml").open("rb") as project_file:
        project_version = tomllib.load(project_file)["project"]["version"]
    version = args.version or project_version
    output_directory = args.output_directory or (
        project_root / "dist" / f"release-linux-amd64-{version}"
    )
    output_directory = output_directory.resolve()
    if output_directory.exists():
        parser.error(f"Folder output sudah ada; pilih folder baru agar hasil tidak tertimpa: {output_directory}")
    output_directory.mkdir(parents=True)

    architecture = subprocess.run(
        ["dpkg", "--print-architecture"], check=True, capture_output=True, text=True
    ).stdout.strip()
    with tempfile.TemporaryDirectory(prefix="docuconvert-linux-build-") as temp_name:
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

        app_bundle = temp_dist / "DocuConvert"
        if not (app_bundle / "DocuConvert").is_file():
            raise RuntimeError(f"PyInstaller tidak menghasilkan executable: {app_bundle}")

        package_root = temp_root / "package-root"
        app_directory = package_root / "opt" / "docuconvert" / "DocuConvert"
        app_directory.parent.mkdir(parents=True)
        shutil.copytree(app_bundle, app_directory, symlinks=True)

        binary_directory = package_root / "usr" / "bin"
        binary_directory.mkdir(parents=True)
        launcher = binary_directory / "docuconvert"
        launcher.write_text(
            "#!/bin/sh\n"
            "cd /opt/docuconvert/DocuConvert\n"
            "exec ./DocuConvert \"$@\"\n",
            encoding="utf-8",
        )
        launcher.chmod(0o755)

        applications = package_root / "usr" / "share" / "applications"
        applications.mkdir(parents=True)
        desktop_entry = applications / "docuconvert.desktop"
        desktop_entry.write_text(
            "[Desktop Entry]\n"
            "Name=DocuConvert\n"
            "Comment=Konversi dan kelola dokumen\n"
            "Exec=docuconvert\n"
            "Icon=docuconvert\n"
            "Terminal=false\n"
            "Type=Application\n"
            "Categories=Office;Utility;\n"
            "StartupNotify=true\n",
            encoding="utf-8",
        )

        icons = package_root / "usr" / "share" / "icons" / "hicolor" / "256x256" / "apps"
        icons.mkdir(parents=True)
        shutil.copy2(
            project_root / "app" / "ui" / "resources" / "icons" / "app-icon.png",
            icons / "docuconvert.png",
        )

        documentation = package_root / "usr" / "share" / "doc" / "docuconvert"
        documentation.mkdir(parents=True)
        shutil.copy2(
            project_root / "THIRD_PARTY_NOTICES.md",
            documentation / "THIRD_PARTY_NOTICES.md",
        )
        shutil.copy2(project_root / "LICENSE", documentation / "LICENSE")
        (documentation / "README").write_text(
            "DocuConvert untuk Debian/Ubuntu x86_64. LibreOffice dipasang sebagai "
            "dependency paket agar konversi Office tersedia.\n",
            encoding="utf-8",
        )

        control_directory = package_root / "DEBIAN"
        control_directory.mkdir()
        (control_directory / "control").write_text(
            "Package: docuconvert\n"
            f"Version: {version}\n"
            f"Architecture: {architecture}\n"
            "Maintainer: DocuConvert\n"
            "Section: utils\n"
            "Priority: optional\n"
            f"Depends: {RUNTIME_DEPENDENCIES}\n"
            "Description: Desktop document converter\n"
            " Local document conversion and PDF tools.\n",
            encoding="utf-8",
        )

        package_name = f"DocuConvert-{version}-linux-{architecture}.deb"
        package_path = output_directory / package_name
        subprocess.run(
            ["dpkg-deb", "--build", "--root-owner-group", str(package_root), str(package_path)],
            check=True,
        )

    checksum = hashlib.sha256(package_path.read_bytes()).hexdigest()
    (output_directory / "SHA256SUMS.txt").write_text(
        f"{checksum}  {package_name}\n", encoding="ascii"
    )
    print(f"Paket Debian/Ubuntu berhasil dibuat: {package_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
