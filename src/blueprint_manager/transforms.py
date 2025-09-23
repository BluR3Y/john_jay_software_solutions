from __future__ import annotations
import re
from typing import Any, Callable, Dict
import pandas as pd


from .exceptions import TransformError


Transform = Callable[[pd.Series, dict], pd.Series]

def _regex_replace(series: pd.Series, params: dict) -> pd.Series:
    pat = params.get("pattern")
    repl = params.get("repl", "")
    flags = params.get("flags", "")
    if pat is None:
        raise TransformError("regex_replace requires `pattern`.")
    re_flags = 0
    if "i" in flags:
        re_flags |= re.IGNORECASE
    return series.astype(str).str.replace(pat, repl, regex=True, flags=re_flags)

def _cast(series: pd.Series, params: dict) -> pd.Series:
    target = params.get("to")
    policy = params.get("on_cast_error", "fail")    # "fail" | "coerce_null" | "drop_row"
    try:
        if target == "integer":
            out = pd.to_numeric(series, errors="raise").astype("Int64")
        elif target == "number":
            out = pd.to_numeric(series, errors="raise").astype(float)
        elif target == "string":
            out = series.astype("string")
        elif target == "boolean":
            out = series.astype("boolean")
        elif target == "date":
            fmt = params.get("format")  # e.g., "%Y-%m-%d"
            out = pd.to_datetime(series, format=fmt, errors="raise" if policy == "fail" else "coerce")
        else:
            raise TransformError(f"Unknown cast target: {target}")
        return out
    except Exception:
        if policy == "coerce_null":
            return pd.Series([pd.NA if v is not None else None for v in series], index=series.index)
        if policy == "drop_row":
            # Signal via special attribute; engine can drop after pipeline
            series.attrs["__drop__"] = True
            return series
        raise

def _titlecase(series: pd.Series, params: dict) -> pd.Series:
    return series.astype(str).str.title()

def _map(series: pd.Series, params: dict) -> pd.Series:
    if not isinstance(params, dict):
        raise TransformError("map transform requires a dict under 'map'")
    return series.map(params).fillna(series)

def _affix(series: pd.Series, params: dict) -> pd.Series:
    """Append or prepend a substring to each value in the series."""
    text = str(params.get("text", ""))
    position = params.get("position", "suffix") # "prefix" or "suffix"
    series = series.astype("string").fillna("")
    if position == "prefix":
        return text + series
    return series + text

REGISTRY: Dict[str, Transform] = {
    "regex_replace": _regex_replace,
    "cast": _cast,
    "titlecase": _titlecase,
    "map": _map,
    "affix": _affix
}

def apply_pipeline(series: pd.Series, steps: list[dict]) -> pd.Series:
    out = series
    for step in steps:
        if not isinstance(step, dict) or len(step) != 1:
            raise TransformError(f"Invalid transform step: {step}")
        name, params = next(iter(step.items()))
        fn = REGISTRY.get(name)
        if fn is None:
            raise TransformError(f"Unknown transform `{name}`")
        out = fn(out, params or {})
    return out