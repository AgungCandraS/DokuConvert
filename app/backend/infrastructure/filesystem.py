"""Safe output naming, isolated job staging, and stale-temp cleanup."""

from __future__ import annotations

import errno
import os
import re
import shutil
import stat
import tempfile
import time
from contextlib import AbstractContextManager
from pathlib import Path

from app.backend.domain.errors import BackendError

_INVALID_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')
_WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL", *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}
_TEMP_ROOT = ".docuconvert-tmp"
_LINK_FALLBACK_ERRNOS = {
    errno.EXDEV,
    errno.EPERM,
    errno.EACCES,
    getattr(errno, "ENOTSUP", 95),
    getattr(errno, "EOPNOTSUPP", 95),
}


def safe_stem(value: str, *, fallback: str = "dokumen") -> str:
    stem = _INVALID_FILENAME.sub("_", value).strip(" .")
    stem = re.sub(r"\s+", " ", stem)[:120].rstrip(" .")
    if not stem:
        stem = fallback
    if stem.split(".", 1)[0].upper() in _WINDOWS_RESERVED_NAMES:
        stem = f"_{stem}"
    return stem


def unique_output_name(directory: Path, filename: str) -> str:
    stem = safe_stem(Path(filename).stem)
    suffix = Path(filename).suffix.lower()
    candidate = f"{stem}{suffix}"
    index = 1
    while (directory / candidate).exists():
        candidate = f"{stem}_{index}{suffix}"
        index += 1
    return candidate


def cleanup_stale_temp_directories(output_directory: Path, *, older_than_seconds: int = 86400) -> None:
    root = output_directory / _TEMP_ROOT
    try:
        root_stat = root.lstat()
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
        return
    cutoff = time.time() - older_than_seconds
    try:
        entries = list(root.iterdir())
    except OSError:
        return
    for entry in entries:
        try:
            entry_stat = entry.lstat()
            if (
                entry.name.startswith("job-")
                and stat.S_ISDIR(entry_stat.st_mode)
                and not stat.S_ISLNK(entry_stat.st_mode)
                and entry_stat.st_mtime < cutoff
            ):
                shutil.rmtree(entry)
        except OSError:
            continue
    try:
        root.rmdir()
    except OSError:
        pass


class JobWorkspace(AbstractContextManager[Path]):
    """A private temporary directory on the destination volume for atomic publish."""

    def __init__(self, output_directory: Path, job_id: str) -> None:
        self.output_directory = output_directory
        self.job_id = job_id
        self.path: Path | None = None

    def __enter__(self) -> Path:
        root = self.output_directory / _TEMP_ROOT
        try:
            try:
                root_stat = root.lstat()
                if not stat.S_ISDIR(root_stat.st_mode) or stat.S_ISLNK(root_stat.st_mode):
                    raise BackendError(
                        "temporary_directory_unavailable",
                        "Folder sementara tidak dapat digunakan.",
                        "Pilih folder output lain atau hapus file .docuconvert-tmp yang ada.",
                    )
            except FileNotFoundError:
                pass
            root.mkdir(mode=0o700, parents=True, exist_ok=True)
            if os.name != "nt":
                root.chmod(0o700)
            self.path = Path(tempfile.mkdtemp(prefix=f"job-{self.job_id}-", dir=root))
            if os.name != "nt":
                self.path.chmod(0o700)
        except OSError as exc:
            raise BackendError(
                "temporary_directory_unavailable",
                "Folder sementara tidak dapat disiapkan.",
                "Pastikan folder output memiliki ruang dan izin tulis.",
                technical_detail=str(exc),
            ) from exc
        return self.path

    def __exit__(self, *_exc: object) -> None:
        if self.path is not None:
            shutil.rmtree(self.path, ignore_errors=True)
            try:
                (self.output_directory / _TEMP_ROOT).rmdir()
            except OSError:
                pass


def publish_outputs(staged_files: list[Path], output_directory: Path) -> list[Path]:
    """Publish completed files atomically, selecting names without overwriting."""
    published: list[Path] = []
    try:
        for staged in staged_files:
            if not staged.is_file() or staged.stat().st_size == 0:
                raise BackendError(
                    "empty_output",
                    "Konverter tidak menghasilkan file yang dapat digunakan.",
                    "Coba lagi dengan file sumber yang valid.",
                )
            while True:
                name = unique_output_name(output_directory, staged.name)
                destination = output_directory / name
                try:
                    os.link(staged, destination)
                    published.append(destination)
                    break
                except FileExistsError:
                    continue
                except OSError as exc:
                    if exc.errno not in _LINK_FALLBACK_ERRNOS:
                        raise
                    # On filesystems without hard-link support, reserve the final
                    # name exclusively and replace only our own reservation.
                    fd = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                    os.close(fd)
                    temp_fd, temporary_name = tempfile.mkstemp(
                        prefix=f".{destination.name}-", suffix=".part", dir=output_directory
                    )
                    os.close(temp_fd)
                    temporary = Path(temporary_name)
                    try:
                        shutil.copyfile(staged, temporary)
                        os.replace(temporary, destination)
                    except Exception:
                        temporary.unlink(missing_ok=True)
                        destination.unlink(missing_ok=True)
                        raise
                    published.append(destination)
                    break
    except Exception:
        for destination in published:
            destination.unlink(missing_ok=True)
        raise
    return published
