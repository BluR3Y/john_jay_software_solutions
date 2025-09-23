from __future__ import annotations
from typing import Any, Dict, List, Callable
import pandas as pd
import numpy as np
import re
from datetime import datetime, date

# ---- Transform registry ---- #
TRANSFORMS: Dict[str, Callable] = {}
ROW_OPS: Dict[str, Callable] = {}

def register(name):
    def deco(fn):
        TRANSFORMS[name] = fn
        return fn
    return deco

def register_row(name):
    def deco(fn):
        ROW_OPS[name] = fn
        return fn
    return deco

# ---- Column transforms ---- #

@register("strip")
def t_strip(s, **_): return s.astype("string").str.strip()

@register("lower")
def t_lower(s, **_): return s.astype("string").str.lower()

@register("upper")
def t_upper(s, **_): return s.astype("string").str.upper()

@register("titlecase")
def t_title(s, **_): 
    return s.astype("string").str.title()

@register("replace")
def t_replace(s, old: str, new: str, regex: bool=False, **_):
    return s.astype("string").str.replace(old, new, regex=regex)

@register("regex_replace")
def t_regex_replace(s, pattern: str, repl: str, flags: str = "", **_):
    f = 0
    if "i" in flags.lower(): f |= re.I
    return s.astype("string").str.replace(re.compile(pattern, f), repl, regex=True)

@register("map")
def t_map(s, mapping: dict, **_):
    out = s.astype("string")
    # wildcard support
    for k, v in mapping.items():
        if "*" in k:
            rx = re.compile("^" + re.escape(k).replace("\*", ".*") + "$", re.I)
            out = out.where(~out.str.match(rx, na=False), v)
        else:
            out = out.mask(out == k, v)
    return out

@register("parse_date")
def t_parse_date(s, format: str | None = None, **_):
    return pd.to_datetime(s, format=format, errors="coerce")

@register("cast")
def t_cast(s, to: str, **_):
    if to == "number":
        return pd.to_numeric(s, errors="coerce")
    if to == "integer":
        return pd.to_numeric(s, errors="coerce").astype("Int64")
    if to == "bool":
        return s.astype("string").str.strip().str.lower().map({
            "true": True, "t": True, "yes": True, "y": True, "1": True,
            "false": False, "f": False, "no": False, "n": False, "0": False
        })
    return s.astype("string")

@register("fillna")
def t_fillna(s, value=None, method=None, **_):
    return s.fillna(value=value).fillna(method=method)

@register("currency_to_number")
def t_currency_to_number(s, **_):
    # Remove $, commas, spaces
    return pd.to_numeric(s.astype("string").str.replace(r"[^0-9\.-]", "", regex=True), errors="coerce")

@register("coalesce")
def t_coalesce(s, others: list[str], df=None, **_):
    cols = [s] + [df[o] for o in others if o in df.columns]
    return pd.concat(cols, axis=1).bfill(axis=1).iloc[:,0]

@register("concat")
def t_concat(s, others: list[str], sep: str = " ", df=None, **_):
    cols = [s.astype("string")] + [df[o].astype("string") for o in others if o in df.columns]
    out = cols[0]
    for c in cols[1:]:
        out = out + sep + c
    return out

@register("compute")
def t_compute(s, expr: str, df=None, **_):
    # Provide helpers in the eval environment
    scope = {
        "len": len,
        "days_between": lambda end, start: (pd.to_datetime(end) - pd.to_datetime(start)).dt.days,
        "today": lambda: pd.Timestamp.today().normalize(),
        "now": lambda: pd.Timestamp.now(),
        "np": np,
        "pd": pd,
    }
    local_df = df.copy()
    local_df["_col"] = s
    # Replace shorthand 'col' with '_col' if the user refers to the current column
    safe_expr = expr.replace("col", "_col")
    result = pd.eval(safe_expr, engine="python", local_dict=local_df, global_dict=scope)
    return result

@register("udf")
def t_udf(s, module: str, func: str, kwargs=None, **_):
    import importlib
    fn = getattr(importlib.import_module(module), func)
    return fn(s, **(kwargs or {}))

def apply_column_plan(df, plan: dict | None):
    if not plan:
        return df
    for col, steps in plan.items():
        if col not in df.columns: 
            continue
        series = df[col]
        for step in steps:
            name, args = next(iter(step.items()))
            fn = TRANSFORMS[name]
            # pass df for transforms that might need other columns
            series = fn(series, df=df, **(args or {}))
        df[col] = series
    return df

# ---- Row operations ---- #

@register_row("drop_if_null")
def rop_drop_if_null(df, cols: list[str], **_):
    return df.dropna(subset=[c for c in cols if c in df.columns])

@register_row("filter")
def rop_filter(df, expr: str, **_):
    # pandas query; user writes e.g., "status == 'Active' and amount > 0"
    return df.query(expr, engine="python")

@register_row("dedupe_on")
def rop_dedupe_on(df, cols: list[str], keep: str = "first", **_):
    return df.drop_duplicates(subset=[c for c in cols if c in df.columns], keep=keep)

def apply_row_plan(df, row_plan: list[dict] | None):
    if not row_plan:
        return df
    for op in row_plan:
        name, args = next(iter(op.items()))
        fn = ROW_OPS[name]
        df = fn(df, **(args or {}))
    return df
