from __future__ import annotations
import pandas as pd
from typing import List, Dict

def _resolve_enum_order(series: pd.Series, order: list[str]):
    cat = pd.Categorical(series, categories=order, ordered=True)
    return cat

def compile_keyed(inputs: List[pd.DataFrame], key: List[str], rules: Dict[str, str], precedence_sources: List[str] | None = None, input_names: List[str] | None = None):
    if not inputs:
        return pd.DataFrame()
    # align columns
    cols = sorted(set().union(*[df.columns for df in inputs]))
    aligned = [df.reindex(columns=cols) for df in inputs]

    # Start with outer-join of all inputs on key
    merged = aligned[0]
    for i, df in enumerate(aligned[1:], start=1):
        merged = merged.merge(df, on=key, how="outer", suffixes=("", f"__r{i}"), validate="1:1")
    
    # resolve per rules
    for col, rule in (rules or {}).items():
        # Collect all variants of the column after merges
        sub = merged.filter(regex=f"^{col}($|__r\d+)")
        if sub.empty:
            continue
        if rule == "first_non_null":
            merged[col] = sub.bfill(axis=1).iloc[:,0]
        elif rule == "max":
            merged[col] = sub.max(axis=1, skipna=True)
        elif rule == "min":
            merged[col] = sub.min(axis=1, skipna=True)
        elif rule.startswith("prefer_enum_order:"):
            order = rule.split(":",1)[1].split(",")
            # pick the "best" according to order by ranking each column then taking min rank
            ranked = sub.apply(lambda s: pd.Categorical(s, categories=order, ordered=True).codes)
            best_idx = ranked.replace(-1, 10**6).idxmin(axis=1)
            merged[col] = merged.lookup(merged.index, best_idx) # deprecated but works; alternative is stack+idx
        else:
            # default: first_non_null
            merged[col] = sub.bfill(axis=1).iloc[:,0]
    
    # After resolution, drop duplicate columns
    keep = []
    seen = set()
    for c in merged.columns:
        if "__r" in c and c.split("__r")[0] in merged.columns:
            continue
        if c in seen:
            continue
        keep.append(c); seen.add(c)
    return merged[keep]