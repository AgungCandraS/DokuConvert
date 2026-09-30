"""Release checks and downloads outside the GUI thread."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import QObject, QThread, QTimer, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices

from app.backend.infrastructure.update_service import UpdateRelease, UpdateService


class _UpdateTask(QThread):
    result = Signal(object)
    failed = Signal(str)
    progress = Signal(int)

    def __init__(self, release: UpdateRelease | None, parent: QObject) -> None:
        super().__init__(parent)
        self.release = release

    def run(self) -> None:
        try:
            service = UpdateService()
            result = (
                service.download(self.release, self.progress.emit, self.isInterruptionRequested)
                if self.release
                else service.check()
            )
            if not self.isInterruptionRequested():
                self.result.emit(result)
        except Exception as exc:
            if not self.isInterruptionRequested():
                self.failed.emit(str(exc))


class UpdateController(QObject):
    checked = Signal(object, bool)
    downloaded = Signal(object)
    failed = Signal(str, bool)
    progress = Signal(int)
    busy_changed = Signal(bool)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self._task: _UpdateTask | None = None
        self._manual = False
        self._downloading = False
        self._closed = False
        self.timer = QTimer(self)
        self.timer.setInterval(5 * 60 * 1000)
        self.timer.timeout.connect(self.check)
        self.timer.start()
        QTimer.singleShot(2000, self.check)

    @property
    def busy(self) -> bool:
        return self._task is not None

    @Slot()
    def check(self, manual: bool = False) -> None:
        if not self.busy and not self._closed:
            self._start(None, manual)

    def download(self, release: UpdateRelease) -> None:
        if not self.busy and not self._closed:
            self._start(release, True)

    def _start(self, release: UpdateRelease | None, manual: bool) -> None:
        self._manual = manual
        self._downloading = release is not None
        self._task = _UpdateTask(release, self)
        self._task.result.connect(self._result)
        self._task.failed.connect(self._failed)
        self._task.progress.connect(self.progress)
        self._task.finished.connect(self._finished)
        self.busy_changed.emit(True)
        self._task.start()

    @Slot(object)
    def _result(self, result: object) -> None:
        if self._downloading:
            self.downloaded.emit(result)
        else:
            self.checked.emit(result, self._manual)

    @Slot(str)
    def _failed(self, message: str) -> None:
        self.failed.emit(message, self._manual)

    @Slot()
    def _finished(self) -> None:
        if self._task is not None:
            self._task.deleteLater()
            self._task = None
        self.busy_changed.emit(False)

    def close(self) -> None:
        self._closed = True
        self.timer.stop()
        if self._task is not None:
            self._task.requestInterruption()
            self._task.wait()


def launch_update(package: Path) -> bool:
    """Start an in-place update; return whether the app should quit."""
    if not getattr(sys, "frozen", False):
        raise ValueError("Pemasangan update tersedia pada aplikasi yang sudah dipaketkan.")
    if sys.platform == "win32":
        directory = Path(sys.executable).resolve().parent
        subprocess.Popen(
            [
                str(package),
                "/VERYSILENT",
                "/SUPPRESSMSGBOXES",
                "/NORESTART",
                "/CLOSEAPPLICATIONS",
                "/UPDATE",
                f"/DIR={directory}",
                f"/LOG={package.parent / 'install.log'}",
            ],
            cwd=package.parent,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        )
        return True
    if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(package))):
        raise OSError("Tidak dapat membuka pengelola paket untuk memasang update.")
    return True
