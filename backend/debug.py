"""Debug mode flag + logger factory for the Ānvīkṣikī backend.

Set DEBUG_MODE=1 (or DEBUG_MODE=true) in the environment or .env to enable
verbose per-step console logging across all backend modules.
"""

from __future__ import annotations

import logging
import os

# ── Flag ─────────────────────────────────────────────────────────────────────

DEBUG_MODE: bool = os.environ.get("DEBUG_MODE", "0").lower() in ("1", "true", "yes")


# ── Logger factory ────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """Return a named logger; DEBUG level when DEBUG_MODE is set."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s  %(levelname)-8s  [%(name)s]  %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.propagate = False
    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    return logger


# ── Banner ────────────────────────────────────────────────────────────────────

if DEBUG_MODE:
    _banner_log = get_logger("anvikshiki.debug")
    _banner_log.debug("=" * 60)
    _banner_log.debug("DEBUG_MODE = ON  — verbose logging active across all modules")
    _banner_log.debug("=" * 60)
