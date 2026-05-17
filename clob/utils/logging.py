"""Logging configuration for clob."""

from __future__ import annotations

import logging

from ..config.settings import CONFIG_DIR

LOG_FILE = CONFIG_DIR / "clob.log"


def setup_logging(level: str = "INFO", log_to_file: bool = True) -> logging.Logger:
    """Configure application logging."""
    logger = logging.getLogger("clob")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if log_to_file:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(LOG_FILE)
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


logger = logging.getLogger("clob")
