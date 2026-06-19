"""Centralised logging configuration for the Eco-Sorter CV Backend."""
from __future__ import annotations

import logging


def setup_logging(level: str) -> logging.Logger:
    """Configure the root logger and return the application logger.

    Args:
        level: Log level name (e.g. ``"INFO"``, ``"DEBUG"``).

    Returns:
        A :class:`logging.Logger` named ``eco_sorter``.
    """
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(fmt=log_format, datefmt=date_format))

    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    # Avoid duplicate handlers on repeated calls
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    return logging.getLogger("eco_sorter")
