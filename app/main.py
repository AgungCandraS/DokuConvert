"""Application composition root for the DocuConvert desktop app."""

import sys

from PySide6.QtCore import QSettings
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.backend.bootstrap import create_backend
from app.backend.config import BackendConfig
from app.ui.controllers.job_controller import JobController
from app.ui.components.common import icon_path
from app.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("DocuConvert")
    app.setOrganizationName("DocuConvert")
    app.setWindowIcon(QIcon(str(icon_path("app-icon.png"))))
    settings = QSettings("DocuConvert", "DocuConvert")
    runtime = create_backend(
        BackendConfig(
            libreoffice_executable=settings.value("libreoffice_executable") or None
        )
    )
    controller = JobController(runtime)
    window = MainWindow(controller)

    def shutdown() -> None:
        controller.close()
        runtime.close(wait_for_jobs=True, cancel_pending=True)

    app.aboutToQuit.connect(shutdown)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
