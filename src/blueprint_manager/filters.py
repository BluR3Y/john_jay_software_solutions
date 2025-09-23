from __future__ import annotations
from typing import Any, Dict
import operator
import pandas as pd


_OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}

def _eval_leaf(df: pd.DataFrame, field: str, cond: Dict[str, Any]) -> pd.Series:
    if "op" in cond:
        op = cond["op"]
        value = cond.get("value")
        if op == "in":
            return df[field].isin(value)
        if op == "not_in":
            return ~df[field].isin(value)
        if op == "is_null":
            return df[field].isna()
        if op == "not_null":
            return ~df[field].isna()
        if op == "between":
            start, end = cond.get("start"), cond.get("end")
            return (df[field] >= start) & (df[field] <= end)
        if op in _OPS:
            return _OPS[op](df[field], value)
        raise ValueError(f"Unsupported operator: {op}")
    raise ValueError("Invalid condition leaf")

def build_mask(df: pd.DataFrame, expr: Dict[str, Any]) -> pd.Series:
    if not expr:
        return pd.Series(True, index=df.index)
    if "AND" in expr:
        masks = [build_mask(df, e) for e in expr["AND"]]
        out = masks[0]
        for m in masks[1:]:
            out = out & m
        return out
    if "OR" in expr:
        masks = [build_mask(df, e) for e in expr["OR"]]
        out = masks[0]
        for m in masks[1:]:
            out = out | m
        return out
    # leaf: { field: { op: X, value: Y } }
    if len(expr) == 1:
        field, cond = next(iter(expr.items()))
        return _eval_leaf(df, field, cond)
    raise ValueError(f"Invalid filter expression: {expr}")