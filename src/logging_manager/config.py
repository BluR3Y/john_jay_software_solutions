from __future__ import annotations
import logging
import os
from typing import Optional
from .handlers import build_console_handler, build_rotating_file_handler
from .formatters import build_formatter

_DEFAULT_FORMAT = "text"  # or "json"

def _str2bool(v: Optional[str], default: bool = False) -> bool:
    if v is None: return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}

def configure_logging(
    level: Optional[str] = None,
    fmt: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10_000_000,
    backups: int = 5,
    propagate_to_root: bool = False,
) -> None:
    """
    Idempotent, safe-to-call multiple times. Respects env vars by default:
      LOG_LEVEL, LOG_FORMAT (text|json), LOG_FILE, LOG_MAX_BYTES, LOG_BACKUPS
    """
    lvl = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    style = (fmt or os.getenv("LOG_FORMAT", _DEFAULT_FORMAT)).lower()
    file_path = log_file or os.getenv("LOG_FILE", "")

    root = logging.getLogger()
    root.setLevel(lvl)

    # Clear existing only if we own them (avoid double handlers during test reloads)
    for h in list(root.handlers):
        root.removeHandler(h)

    formatter = build_formatter(style=style)

    # Console handler (always)
    ch = build_console_handler(formatter)
    root.addHandler(ch)

    # Optional rotating file handler
    if file_path:
        mb = int(os.getenv("LOG_MAX_BYTES", max_bytes))
        bk = int(os.getenv("LOG_BACKUPS", backups))
        fh = build_rotating_file_handler(file_path, formatter, mb, bk)
        root.addHandler(fh)

    # Don’t let child package loggers double-send to root unless explicitly desired
    root.propagate = _str2bool(os.getenv("LOG_PROPAGATE"), propagate_to_root)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

def set_level(level: str) -> None:
    logging.getLogger().setLevel(level.upper())
