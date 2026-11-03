"""Simple structured (key=value) logging to stderr."""

from __future__ import annotations

import logging
import sys
from typing import Any

_LOGGER_NAME = "chemiproof"


def get_logger() -> logging.Logger:
    logger = logging.getLogger(_LOGGER_NAME)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(asctime)sZ level=%(levelname)s %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def log_event(event: str, **fields: Any) -> None:
    """Log `event` with sorted key=value fields so logs are greppable and deterministic."""
    parts = [f"event={event}", *(f"{k}={fields[k]!r}" for k in sorted(fields))]
    get_logger().info(" ".join(parts))
