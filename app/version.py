"""Runtime version, stamped with the release version by PyInstaller."""

from pathlib import Path

_stamp = Path(__file__).with_name("VERSION")
VERSION = _stamp.read_text(encoding="utf-8").strip() if _stamp.is_file() else "0.1.1"
