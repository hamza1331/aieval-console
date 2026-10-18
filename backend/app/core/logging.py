"""Structured, privacy-conscious logging configuration."""

import logging
import sys


def setup_logging() -> None:
    """Configures structured application logging."""
    logger = logging.getLogger("aieval_console")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)


logger = logging.getLogger("aieval_console")

