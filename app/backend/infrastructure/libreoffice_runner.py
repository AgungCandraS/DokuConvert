"""Isolated, headless LibreOffice invocation with cooperative cancellation."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from app.backend.application.progress import ProgressReporter
from app.backend.domain.errors import BackendError, JobCancelled
from app.backend.domain.models import EnvironmentCheck


def find_libreoffice(preferred_path: str | os.PathLike[str] | None = None) -> str | None:
    # Prefer the copy shipped with DocuConvert over machine-specific settings.
    # This keeps a portable build independent from stale paths saved on the build PC.
    bundled = bundled_libreoffice_path()
    if bundled:
        return str(bundled)

    candidates = [preferred_path, os.environ.get("DOCUCONVERT_LIBREOFFICE_PATH")]
    for candidate in candidates:
        if candidate:
            path = Path(candidate).expanduser()
            if path.is_file() and path.name.lower() in {"soffice.exe", "soffice.com", "soffice"}:
                if os.name == "nt" and path.name.lower() in {"soffice.com", "soffice"}:
                    windowless = path.with_name("soffice.exe")
                    if windowless.is_file():
                        path = windowless
                return str(path.resolve())
    executable = (
        shutil.which("soffice.exe") or shutil.which("soffice.com") or shutil.which("soffice")
    )
    if executable:
        return str(Path(executable).resolve())
    if os.name == "nt":
        roots = {os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)")}
        for root in filter(None, roots):
            candidate = Path(root) / "LibreOffice" / "program" / "soffice.exe"
            if candidate.is_file():
                return str(candidate)
    elif sys.platform == "darwin":
        for candidate in (
            Path("/Library/Application Support/DocuConvert/LibreOffice.app/Contents/MacOS/soffice"),
            Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
            Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice",
        ):
            if candidate.is_file():
                return str(candidate.resolve())
    return None


def bundled_libreoffice_path() -> Path | None:
    for candidate in _bundled_libreoffice_candidates():
        if candidate.is_file():
            return candidate.resolve()
    return None


def is_bundled_libreoffice(executable: str | os.PathLike[str] | None) -> bool:
    if not executable:
        return False
    try:
        selected = Path(executable).resolve()
        return any(
            candidate.is_file() and candidate.resolve() == selected
            for candidate in _bundled_libreoffice_candidates()
        )
    except OSError:
        return False


def _bundled_libreoffice_candidates() -> list[Path]:
    """Locate an optional LibreOffice distribution shipped beside the application."""
    roots = [Path.cwd(), Path(__file__).resolve().parents[3]]
    if getattr(sys, "frozen", False):
        roots.insert(0, Path(sys.executable).resolve().parent)
    extraction_root = getattr(sys, "_MEIPASS", None)
    if extraction_root:
        roots.insert(0, Path(extraction_root))

    candidates: list[Path] = []
    if sys.platform == "darwin" and getattr(sys, "frozen", False):
        app_contents = Path(sys.executable).resolve().parent.parent
        candidates.append(
            app_contents
            / "Resources"
            / "tools"
            / "libreoffice"
            / "LibreOffice.app"
            / "Contents"
            / "MacOS"
            / "soffice"
        )
    if os.name == "nt":
        executable_names = ("soffice.exe", "soffice.com")
        relative_paths = (
            Path("tools") / "LibreOffice" / "program",
            Path("LibreOffice") / "program",
        )
    else:
        executable_names = ("soffice",)
        relative_paths = (
            Path("tools") / "libreoffice" / "program",
            Path("LibreOffice") / "program",
        )

    for root in roots:
        for relative_path in relative_paths:
            for executable_name in executable_names:
                candidates.append(root / relative_path / executable_name)
    if sys.platform == "darwin":
        candidates.extend(
            (
                Path("/Library/Application Support/DocuConvert/LibreOffice.app/Contents/MacOS/soffice"),
                Path("/Applications/LibreOffice.app/Contents/MacOS/soffice"),
                Path.home() / "Applications/LibreOffice.app/Contents/MacOS/soffice",
            )
        )
    return candidates


class LibreOfficeRunner:
    def __init__(
        self,
        *,
        timeout_seconds: int = 300,
        executable: str | None = None,
        preferred_path: str | None = None,
    ) -> None:
        self.executable = executable or find_libreoffice(preferred_path)
        self.timeout_seconds = timeout_seconds

    def validate_environment(self) -> EnvironmentCheck:
        return EnvironmentCheck(
            "LibreOffice",
            self.executable is not None,
            "LibreOffice siap digunakan." if self.executable else "LibreOffice belum ditemukan.",
            self.executable,
        )

    def convert_to_pdf(self, source: Path, destination_directory: Path, reporter: ProgressReporter) -> Path:
        if not self.executable:
            raise BackendError(
                "libreoffice_missing",
                "LibreOffice belum terpasang atau tidak ditemukan.",
                "Pasang LibreOffice, lalu mulai ulang aplikasi.",
            )
        with tempfile.TemporaryDirectory(prefix="lo-profile-") as profile_directory:
            profile_uri = Path(profile_directory).resolve().as_uri()
            command = [
                self.executable,
                "--headless",
                "--nologo",
                "--nodefault",
                "--nolockcheck",
                "--norestore",
                f"-env:UserInstallation={profile_uri}",
                "--convert-to",
                "pdf",
                "--outdir",
                str(destination_directory),
                str(source),
            ]
            with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
                creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
                try:
                    process = subprocess.Popen(
                        command,
                        stdin=subprocess.DEVNULL,
                        stdout=stdout_file,
                        stderr=stderr_file,
                        shell=False,
                        creationflags=creation_flags,
                    )
                except OSError as exc:
                    raise BackendError(
                        "libreoffice_start_failed",
                        "LibreOffice tidak dapat dijalankan.",
                        "Pastikan instalasi LibreOffice berfungsi dengan baik.",
                        technical_detail=str(exc),
                    ) from exc
                started = time.monotonic()
                while process.poll() is None:
                    if reporter.cancelled:
                        self._stop_process(process)
                        raise JobCancelled
                    if time.monotonic() - started > self.timeout_seconds:
                        self._stop_process(process)
                        raise BackendError(
                            "conversion_timeout",
                            f"Konversi {source.name} melewati batas waktu.",
                            "Coba file yang lebih kecil atau pastikan file tidak rusak.",
                        )
                    time.sleep(0.1)
                if process.returncode != 0:
                    stderr_file.seek(0)
                    detail = stderr_file.read(4096).decode(errors="replace").strip()
                    raise BackendError(
                        "office_conversion_failed",
                        f"File {source.name} tidak dapat dikonversi.",
                        "Buka file di LibreOffice untuk memastikan file tidak rusak atau terkunci.",
                        technical_detail=detail,
                    )

        output = destination_directory / f"{source.stem}.pdf"
        if not output.is_file() or output.stat().st_size == 0:
            raise BackendError(
                "office_output_missing",
                f"LibreOffice tidak menghasilkan PDF untuk {source.name}.",
                "Periksa apakah file sumber dapat dibuka di LibreOffice.",
            )
        reporter.check_cancelled()
        return output

    @staticmethod
    def _stop_process(process: subprocess.Popen[bytes]) -> None:
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=3)
