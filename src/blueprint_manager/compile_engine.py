from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd

from .fuzzy import fuzzy_match_series
from .textnorm import normalize
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

def _enrich(df: pd.DataFrame, frames: dict[str, pd.DataFrame], steps: list[dict]) -> pd.DataFrame:
    out = df.copy()
    for step in steps or []:
        src_name = step["from"]
        left_on  = step["left_on"]
        right_on = step["right_on"]
        add_map  = step.get("add", {})
        how      = step.get("how", "left")
        match    = step.get("match") or {"strategy": ["exact"]}

        dim = frames[src_name].copy()
        # Keep right key + needed columns
        need_cols = {right_on} | set(add_map.values())
        dim = dim[[c for c in need_cols if c in dim.columns]].drop_duplicates(subset=[right_on])

        # Fast path: exact join only
        if match.get("strategy", ["exact"]) == ["exact"]:
            merged = out.merge(dim, how=how, left_on=left_on, right_on=right_on, suffixes=("", "_dim"))
            for new_col, src_col in add_map.items():
                merged.rename(columns={src_col: new_col}, inplace=True)
            merged.drop(columns=[right_on], inplace=True, errors="ignore")
            out = merged
            continue

        # Build match result against dim[right_on]
        strategies = match.get("strategy", ["exact","normalized","fuzzy"])
        norm_steps = match.get("normalize", ["strip","lower","collapse_ws","strip_punct"])
        fuzzy_cfg  = match.get("fuzzy", {})
        scorer     = fuzzy_cfg.get("scorer", "token_sort_ratio")
        threshold  = int(fuzzy_cfg.get("threshold", 90))
        top_k      = int(fuzzy_cfg.get("top_k", 1))
        block      = fuzzy_cfg.get("block", "first_char")

        # Produce a match-to column (value from dim[right_on])
        match_to, match_score, match_method = fuzzy_match_series(
            out[left_on].astype(object),
            dim[right_on].astype(object),
            normalize_steps=norm_steps,
            scorer=scorer,
            threshold=threshold,
            top_k=top_k,
            block=block,
        )

        # Join via matched right value
        out["_match_key_tmp"] = match_to
        merged = out.merge(dim, how="left", left_on="_match_key_tmp", right_on=right_on, suffixes=("", "_dim"))
        out = merged.drop(columns=["_match_key_tmp", right_on], errors="ignore")
        # Rename ‘add’ columns
        for new_col, src_col in add_map.items():
            out.rename(columns={src_col: new_col}, inplace=True)

        # Audit columns if requested
        if match.get("audit"):
            base = left_on
            out[f"{base}_match_to"] = match_to
            out[f"{base}_match_score"] = match_score
            out[f"{base}_match_method"] = match_method

        # on_miss policy
        on_miss = match.get("on_miss", "leave_null")
        if on_miss == "fail":
            # fail if any ‘add’ column is null while left had a non-null candidate
            for new_col in add_map.keys():
                bad = out[left_on].notna() & out[new_col].isna()
                if bad.any():
                    sample = out.loc[bad, [left_on]].head(5).to_dict(orient="records")
                    raise ValueError(f"Fuzzy enrich missed matches for {left_on}→{src_name}. Examples: {sample}")
        # keep_source/leave_null require no action; the computed codes remain NaN when no match
    return out


class Compiler:
    def __init__(self, frames: dict[str, pd.DataFrame]):
        self.frames = frames    # raw sources
        self.compiled = {}      # hold compiled targets


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

        # Allow enrich using both raw + compiled
        enrich_steps = cfg.get("enrich") or []
        merged = _enrich(merged, {**self.frames, **self.compiled}, enrich_steps)

        if post_filter:
            mask = build_mask(merged, post_filter)
            merged = merged[mask].copy()
        
        # Save it for later enrich steps
        self.compiled[cfg["name"]] = merged
        return merged