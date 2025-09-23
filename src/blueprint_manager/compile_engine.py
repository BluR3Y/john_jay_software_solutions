from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd


from .filters import build_mask
from modules.script_logger import logger
log = logger.get_logger()




def _apply_filters(per_table_frames: dict[str, pd.DataFrame], pre_filter_cfg: Dict[str, Any] | None) -> dict[str, pd.DataFrame]:
    if not pre_filter_cfg:
        return per_table_frames
    out: dict[str, pd.DataFrame] = {}
    for table_id, df in per_table_frames.items():
        expr = pre_filter_cfg.get(table_id)
        if expr:
            mask = build_mask(df, expr)
            out[table_id] = df[mask].copy()
        else:
            out[table_id] = df
    return out




def _merge_inputs(inputs: list[str], frames: dict[str, pd.DataFrame], key: list[str]) -> pd.DataFrame:
    # Outer merge on prioritized order, keeping all rows; later sources fill nulls
    merged = None
    for i, src in enumerate(inputs):
        df = frames[src]
        if merged is None:
            merged = df.copy()
        else:
            merged = merged.merge(df, how="outer", on=key, suffixes=("", f"__{i}"))
    return merged if merged is not None else pd.DataFrame()




def _apply_merge_rules(df: pd.DataFrame, rules: Dict[str, Any], inputs: list[str]) -> pd.DataFrame:
    if not rules:
        return df
    out = df.copy()
    for field, rule in rules.items():
        if isinstance(rule, str) and rule == "first_non_null":
            # pick first non-null across candidate columns for field
            candidates = [col for col in df.columns if col.split("__")[0] == field]
            if not candidates and field in df.columns:
                continue
            if candidates:
                out[field] = df[candidates].bfill(axis=1).iloc[:, 0]
            elif isinstance(rule, str):
                # treat as prefer_source table_id
                preferred = rule
                cols = [c for c in df.columns if c == field or c.startswith(field+"__")]
                if field in df.columns:
                    out[field] = df[field]
                for i, col in enumerate(cols):
                    if col == field:
                        continue
                    if preferred in col:
                        out[field] = df[col]
                        break
            elif isinstance(rule, dict):
                strat = rule.get("strategy")
                if strat == "first_non_null":
                    priority = rule.get("priority") or []
                    cols = [field] + [f"{field}__{inputs.index(src)}" for src in inputs if src in priority]
                    cols = [c for c in cols if c in df.columns]
                    if cols:
                        out[field] = df[cols].bfill(axis=1).iloc[:, 0]
                elif strat == "prefer_source":
                    src = rule.get("prefer_source")
                    cols = [field] + [c for c in df.columns if c.startswith(field+"__")]
                    pick = next((c for c in cols if src and src in c), cols[0] if cols else None)
                    if pick:
                        out[field] = df[pick]
        # else: ignore
    # Drop suffixed columns
    keep = [c for c in out.columns if "__" not in c]
    return out[keep]

class Compiler:
    def __init__(self, frames: dict[str, pd.DataFrame]):
        self.frames = frames


    def compile_target(self, cfg: Dict[str, Any]) -> pd.DataFrame:
        name = cfg.get("name")
        key = cfg.get("key") or []
        inputs = cfg.get("inputs") or []
        pre_filter = cfg.get("pre_filter") or {}
        post_filter = cfg.get("post_filter") or {}
        merge_rules = cfg.get("merge_rules") or {}


        log.info(f"Compiling target: {name}")
        filtered = _apply_filters({i: self.frames[i] for i in inputs}, pre_filter)
        merged = _merge_inputs(inputs, filtered, key)
        merged = _apply_merge_rules(merged, merge_rules, inputs)
        if post_filter:
            mask = build_mask(merged, post_filter)
            merged = merged[mask].copy()
        return merged