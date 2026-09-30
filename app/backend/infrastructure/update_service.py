"""Check public releases and download verified, platform-specific update packages."""

from __future__ import annotations

import hashlib
import json
import platform
import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from app.backend.config import user_data_directory
from app.version import VERSION

REPOSITORY = "AgungCandraS/DokuConvert"
RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
DOWNLOAD_PREFIX = f"https://github.com/{REPOSITORY}/releases/download/"
MAX_PACKAGE_SIZE = 4 * 1024**3


@dataclass(frozen=True)
class UpdateRelease:
    version: str
    asset_name: str
    download_url: str
    size: int
    sha256: str


def version_tuple(value: str) -> tuple[int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("Versi rilis harus menggunakan format x.y.z.")
    return tuple(int(part) for part in match.groups())


def platform_asset(system: str | None = None, machine: str | None = None) -> str:
    system = system or platform.system()
    machine = (machine or platform.machine()).lower()
    if system == "Windows" and machine in {"amd64", "x86_64"}:
        return "DocuConvert-Windows-x64.exe"
    if system == "Darwin":
        if machine in {"arm64", "aarch64"}:
            return "DocuConvert-macOS-Apple-Silicon.pkg"
        if machine in {"x86_64", "amd64"}:
            return "DocuConvert-macOS-Intel.pkg"
    if system == "Linux" and machine in {"x86_64", "amd64"}:
        return "DocuConvert-Linux-amd64.deb"
    raise ValueError("Belum ada paket update untuk sistem dan arsitektur ini.")


def _request(url: str) -> Request:
    return Request(url, headers={"User-Agent": f"DocuConvert/{VERSION}"})


def _asset_url(asset: dict) -> str:
    url = str(asset.get("browser_download_url", ""))
    if not url.startswith(DOWNLOAD_PREFIX):
        raise ValueError("Alamat paket update tidak berasal dari repository resmi.")
    return url


class UpdateService:
    def check(self, current_version: str = VERSION) -> UpdateRelease | None:
        try:
            with urlopen(_request(RELEASE_API), timeout=15) as response:
                payload = json.loads(response.read(1024 * 1024))
        except HTTPError as exc:
            if exc.code == 404:
                return None  # A repository without any published releases.
            raise
        if payload.get("draft") or payload.get("prerelease"):
            return None
        version = str(payload["tag_name"])
        if version_tuple(version) <= version_tuple(current_version):
            return None
        name = platform_asset()
        assets = payload.get("assets", [])
        asset = next((item for item in assets if item.get("name") == name), None)
        if asset is None:
            raise ValueError("Rilis baru tersedia, tetapi paket untuk perangkat ini belum siap.")
        url = _asset_url(asset)
        size = int(asset["size"])
        if not 0 < size <= MAX_PACKAGE_SIZE:
            raise ValueError("Ukuran paket update tidak valid.")
        digest = str(asset.get("digest") or "").removeprefix("sha256:")
        if not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            checksums = next(
                (item for item in assets if item.get("name") == "SHA256SUMS.txt"), None
            )
            if checksums is None:
                raise ValueError("Checksum paket update belum tersedia.")
            with urlopen(_request(_asset_url(checksums)), timeout=15) as response:
                lines = response.read(64 * 1024).decode("utf-8").splitlines()
            digest = ""
            for line in lines:
                parts = line.split(maxsplit=1)
                if len(parts) == 2 and parts[1].lstrip("*") == name:
                    digest = parts[0]
                    break
        if not re.fullmatch(r"[a-fA-F0-9]{64}", digest):
            raise ValueError("Checksum paket update tidak valid.")
        return UpdateRelease(version.lstrip("v"), name, url, size, digest.lower())

    def download(
        self,
        release: UpdateRelease,
        progress: Callable[[int], None],
        cancelled: Callable[[], bool],
    ) -> Path:
        root = user_data_directory() / "updates"
        root.mkdir(parents=True, exist_ok=True)
        # An isolated directory also prevents running an incomplete prior download.
        directory = Path(tempfile.mkdtemp(prefix="release-", dir=root))
        partial = directory / (release.asset_name + ".part")
        target = directory / release.asset_name
        digest = hashlib.sha256()
        received = 0
        try:
            with (
                urlopen(_request(release.download_url), timeout=15) as response,
                partial.open("xb") as output,
            ):
                while True:
                    if cancelled():
                        raise InterruptedError("Unduhan update dibatalkan.")
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    received += len(chunk)
                    if received > release.size:
                        raise ValueError("Ukuran unduhan melebihi ukuran paket update.")
                    digest.update(chunk)
                    output.write(chunk)
                    progress(int(received * 100 / release.size))
            if received != release.size or digest.hexdigest() != release.sha256:
                raise ValueError("Verifikasi update gagal. Coba unduh kembali.")
            partial.replace(target)
            return target
        except Exception:
            partial.unlink(missing_ok=True)
            directory.rmdir()
            raise
