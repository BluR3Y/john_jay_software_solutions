from __future__ import annotations
from typing import Any, Dict, List, Union
import math
import numpy as np
import pandas as pd
from pandas.api import types as ptypes

class ExprError(Exception): pass

Node = Union[dict, list, int, float, str, bool, None]

def _to_series(df: pd.DataFrame, x: Any) -> pd.Series:
    if isinstance(x, pd.Series):
        return x
    if x is None or isinstance(x, (int, float, str, bool)):
        # broadcast scalar to Series of correct index
        return pd.Series([x] * len(df), index=df.index)
    raise ExprError(f"Cannot broadcast value of type {type(x)}")

def _col(df: pd.DataFrame, name: str) -> pd.Series:
    if name not in df.columns:
        raise ExprError(f"Unknown column in expression: {name}")
    return df[name]

def _as_ast(node: Node) -> dict:
    # Normalize short array form: ["add", a, b] -> {"op":"add","args":[a,b]}
    if isinstance(node, list):
        if not node:
            raise ExprError("Empty expression array")
        op = node[0]
        return {"op": str(op), "args": node[1:]}
    if isinstance(node, dict):
        return node
    # primitives allowed
    return {"op": "lit", "args": [node]}

def eval_expr(df: pd.DataFrame, node: Node) -> pd.Series:
    ast = _as_ast(node)
    op = ast.get("op")
    args = ast.get("args", [])

    # literals
    if op == "lit":
        return _to_series(df, args[0] if args else None)

    # column ref
    if "col" in ast:
        return _col(df, ast["col"])

    # ---------- SPECIAL-CASE IF (lazy) ----------
    if op == "if":
        if len(args) < 2:
            raise ExprError("if expects at least 2 args: ['if', cond, then, else?]")
        cond = eval_expr(df, args[0]).astype("boolean")
        then_val = eval_expr(df, args[1]) if len(args) > 1 else _to_series(df, None)
        else_val = eval_expr(df, args[2]) if len(args) > 2 else _to_series(df, None)
        return then_val.where(cond, else_val)
    # --------------------------------------------

    # For all other ops, now evaluate arguments
    ev = [eval_expr(df, a) if isinstance(a, (dict, list)) else _to_series(df, a) for a in args]

    # arithmetic
    if op == "add":
        out = ev[0]
        for s in ev[1:]:
            out = out + s
        return out
    if op == "sub": return ev[0] - ev[1]
    if op == "mul":
        out = ev[0]
        for s in ev[1:]:
            out = out * s
        return out
    if op == "div": return ev[0] / ev[1]
    if op == "pow": return ev[0] ** ev[1]
    if op == "neg": return -ev[0]
    if op == "abs": return ev[0].abs()
    if op == "round":
        nd = int(args[1]) if len(args) > 1 and not isinstance(args[1], (dict, list)) else 0
        return ev[0].round(nd)

    # comparison (NA-aware; avoids object-casting unless needed)
    if op == "eq":  return ev[0].eq(ev[1])
    if op == "neq": return ev[0].ne(ev[1])
    if op == "gt":  return ev[0] > ev[1]
    if op == "gte": return ev[0] >= ev[1]
    if op == "lt":  return ev[0] < ev[1]
    if op == "lte": return ev[0] <= ev[1]

    # boolean
    if op == "and":
        out = ev[0].astype("boolean")
        for s in ev[1:]:
            out = out & s.astype("boolean")
        return out
    if op == "or":
        out = ev[0].astype("boolean")
        for s in ev[1:]:
            out = out | s.astype("boolean")
        return out
    if op == "not":
        return (~ev[0].astype("boolean")).astype("boolean")

    # null handling
    if op == "coalesce":
        out = ev[0]
        for s in ev[1:]:
            out = out.fillna(s)
        return out
    if op == "fillna":
        return ev[0].fillna(ev[1])
    if op == "is_null":
        return ev[0].isna()
    if op == "not_null":
        return ~ev[0].isna()

    # strings
    if op == "concat":
        parts = [s.astype("string") for s in ev]
        out = parts[0]
        for s in parts[1:]:
            out = out.str.cat(s, na_rep="")
        return out
    if op == "len":
        return ev[0].astype("string").str.len()

    # dates
    if op == "strftime":
        fmt = args[0] if isinstance(args[0], str) else "%Y-%m-%d"
        ser = ev[1] if len(ev) > 1 else ev[0]
        ser = pd.to_datetime(ser, errors="coerce")
        return ser.dt.strftime(fmt)
    if op == "datediff":
        unit = (args[0] if isinstance(args[0], str) else "day").lower()
        end = pd.to_datetime(ev[1], errors="coerce")
        start = pd.to_datetime(ev[2], errors="coerce")
        delta = (end - start)
        if unit == "day": return delta.dt.days
        if unit == "hour": return (delta.dt.total_seconds() / 3600)
        if unit == "minute": return (delta.dt.total_seconds() / 60)
        raise ExprError(f"Unsupported datediff unit: {unit}")

    # misc
    if op == "clip":
        base = ev[0]
        minv = ev[1] if len(ev) > 1 else None
        maxv = ev[2] if len(ev) > 2 else None
        return base.clip(lower=minv if minv is not None else -np.inf,
                         upper=maxv if maxv is not None else  np.inf)
    if op == "percent":
        return ev[0] * ev[1]

    raise ExprError(f"Unknown op: {op}")
