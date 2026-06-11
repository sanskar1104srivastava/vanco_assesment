"""Shared logging helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from .config import get_settings


_CONFIGURED = False


def configure_logging() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    Path(settings.logs_path).mkdir(parents=True, exist_ok=True)
    log_file = Path(settings.logs_path) / "hybrid_rag.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)

