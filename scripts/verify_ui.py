"""Render desktop themes and dropdowns without starting network checks."""

import os
import sys
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtGui import QFont, QFontDatabase  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

from app.ui.main_window import MainWindow  # noqa: E402
from app.ui.tool_catalog import TOOL_BY_KEY  # noqa: E402


def main() -> int:
    app = QApplication([])
    app.setStyle("Fusion")
    # The offscreen Qt plugin has no system font database on Windows.
    fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    for filename in ("segoeui.ttf", "segoeuib.ttf", "segoeuisb.ttf"):
        if (fonts / filename).is_file():
            QFontDatabase.addApplicationFont(str(fonts / filename))
    font = QFont()
    font.setFamilies(["Segoe UI", "Inter", "Roboto", "Calibri"])
    app.setFont(font)
    output = Path(__file__).resolve().parents[1] / "build" / "ui-verification"
    output.mkdir(parents=True, exist_ok=True)
    with patch("app.ui.controllers.update_controller.UpdateService.check", return_value=None):
        window = MainWindow()
        window.updates.close()
        window.show()
        for dark in (False, True):
            window.dark_mode = dark
            window._apply_theme()
            window._open_tool_dialog(TOOL_BY_KEY["watermark_pdf"].name)
            app.processEvents()
            theme = "dark" if dark else "light"
            window.grab().save(str(output / f"{theme}.png"))
            combo = window.job_page.watermark_position
            combo.showPopup()
            app.processEvents()
            combo.view().window().grab().save(str(output / f"{theme}-dropdown.png"))
            combo.hidePopup()
        window.close()
    print(f"UI renders saved: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
