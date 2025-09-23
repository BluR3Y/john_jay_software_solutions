from __future__ import annotations
import contextvars
from typing import Optional

_corr: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("corr_id", default=None)

def set_correlation_id(corr_id: Optional[str]) -> None:
    _corr.set(corr_id)

def get_correlation_id() -> Optional[str]:
    return _corr.get()

def clear_correlation_id() -> None:
    _corr.set(None)
