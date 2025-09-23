from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler

def build_console_handler(formatter: logging.Formatter) -> logging.Handler:
    h = logging.StreamHandler()
    h.setFormatter(formatter)
    h.setLevel(logging.NOTSET)
    return h

def build_rotating_file_handler(path: str, formatter: logging.Formatter,
                                max_bytes: int, backups: int) -> logging.Handler:
    h = RotatingFileHandler(path, maxBytes=max_bytes, backupCount=backups, encoding="utf-8")
    h.setFormatter(formatter)
    h.setLevel(logging.INFO)
    return h
