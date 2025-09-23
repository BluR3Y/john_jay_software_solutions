from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd


from .filters import build_mask
from modules.script_logger import logger
log = logger.get_logger()




class Comparator:
    def __init__(self, compiled: dict[str, pd.DataFrame]):
        self.compiled = compiled


    def compare_pair(self, cfg: Dict[str, Any]) -> pd.DataFrame:
        left = cfg.get("left")
        right = cfg.get("right")
        on = cfg.get("on") or []
        filt = cfg.get("filter") or {}
        log.info(f"Comparing {left} vs {right} on {on}")
        ldf = self.compiled[left]
        rdf = self.compiled[right]
        if filt:
            ldf = ldf[build_mask(ldf, filt)]
            rdf = rdf[build_mask(rdf, filt)]
        merged = ldf.merge(rdf, how="outer", on=on, suffixes=("__left", "__right"))
        # Identify discrepancies for overlapping columns
        diff_cols = []
        for col in ldf.columns:
            if col in on:
                continue
            if col in rdf.columns:
                lc = f"{col}__left"
                rc = f"{col}__right"
                if lc in merged.columns and rc in merged.columns:
                    merged[f"__eq__:{col}"] = merged[lc].astype(str) == merged[rc].astype(str)
                    diff_cols.append(col)
        # Keep rows with any inequality in compared columns
        if diff_cols:
            mask = ~merged[[f"__eq__:{c}" for c in diff_cols]].all(axis=1)
            merged = merged[mask]
        return merged