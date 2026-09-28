"""Private rotating application log configuration without file contents or paths."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(log_directory: Path, *, level: int = logging.INFO) -> logging.Logger:
    log_directory = Path(log_directory)
    log_directory.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("docuconvert.backend")
    logger.setLevel(level)
    logger.propagate = False
    if not any(getattr(handler, "baseFilename", None) == str(log_directory / "backend.log") for handler in logger.handlers):
        handler = RotatingFileHandler(
            log_directory / "backend.log", maxBytes=2_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger

