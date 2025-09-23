from __future__ import annotations
import pandas as pd
from typing import List, Dict, Any

def keyed_diff(left: pd.DataFrame, right: pd.DataFrame, on: List[str]) -> Dict[str, Any]:
    merged = left.merge(right, on=on, how="outer", suffixes=("_l", "_r"), indicator=True)
    added = merged.loc[merged["_merge"] == "right_only", on]
    removed = merged.loc[merged["_merge"] == "left_only", on]

    both = merged.loc[merged["_merge"] == "both"].copy()
    changes: Dict[str, pd.DataFrame] = {}
    for col in left.columns:
        if col in on: 
            continue
        lcol, rcol = f"{col}_l", f"{col}_r"
        if lcol in both.columns and rcol in both.columns:
            diff_mask = (both[lcol] != both[rcol]) & ~(both[lcol].isna() & both[rcol].isna())
            diffs = both.loc[diff_mask, on + [lcol, rcol]]
            if not diffs.empty:
                changes[col] = diffs
    return {"added": added, "removed": removed, "changes": changes}