# src/data_manager/textnorm.py
from __future__ import annotations
import re
import unicodedata

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s]")

def normalize(s: str | None, steps: list[str]) -> str | None:
    if s is None:
        return None
    out = s
    if "nfkc" in steps:
        out = unicodedata.normalize("NFKC", out)
    if "strip" in steps:
        out = out.strip()
    if "lower" in steps:
        out = out.lower()
    if "collapse_ws" in steps:
        out = _WS_RE.sub(" ", out)
    if "strip_punct" in steps:
        out = _PUNCT_RE.sub("", out)
    return out
