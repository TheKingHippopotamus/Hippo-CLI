from __future__ import annotations

import logging
from typing import Optional

from rich.logging import RichHandler


def setup_logging(level: str = "INFO") -> None:
    """Configure application-wide logging with sensible defaults."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True, markup=True)],
    )


def get_logger(name: Optional[str] = None, level: str = "INFO") -> logging.Logger:
    """Return a logger after ensuring the root configuration is set."""
    if not logging.getLogger().handlers:
        setup_logging(level)
    return logging.getLogger(name or __name__)

