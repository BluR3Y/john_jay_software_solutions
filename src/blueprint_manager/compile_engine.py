from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd

from .fuzzy import fuzzy_match_series
from .textnorm import normalize
from .filters import build_mask
from .plugins import ENRICH_PLUGINS
from .enrich import enrich_join
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


def _apply_enrich(df: pd.DataFrame, frames: dict[str, pd.DataFrame], steps: list[dict]) -> pd.DataFrame:
    out = df.copy()
    for step in steps or []:
        # Two modes:
        # 1) Built-in join-based enrich:
        if "from" in step and "left_on" in step and "right_on" in step:
            src = step["from"]
            if src not in frames:
                raise ValueError(f"Enrich source '{src}' not found among frames: {list(frames.keys())}")
            dim = frames[src]
            out = enrich_join(
                out, dim,
                left_on=step["left_on"],
                right_on=step["right_on"],
                add_map=step.get("add", {}),
                how=step.get("how", "left"),
                match=step.get("match"),
            )
            continue

        # 2) Plugin enrichers by name:
        if "fn" in step:
            fn = ENRICH_PLUGINS.get(step["fn"])
            if fn is None:
                raise ValueError(f"Unknown enrich fn: {step['fn']}")
            out = fn(out, step.get("params", {}), frames=frames)  # signature: (df, params) -> df
            continue

        raise ValueError(f"Invalid enrich step: {step}")
    return out

class Compiler:
    def __init__(self, frames: dict[str, pd.DataFrame]):
        self.frames = frames
        self.compiled: dict[str, pd.DataFrame] = {}

    def compile_target(self, cfg: Dict[str, Any]) -> pd.DataFrame:
        name = cfg.get("name")
        key = cfg.get("key") or []
        inputs = cfg.get("inputs") or []
        pre_filter = cfg.get("pre_filter") or {}
        post_filter = cfg.get("post_filter") or {}
        merge_rules = cfg.get("merge_rules") or {}

        log.info(f"Compiling target: {name}")

        # Validate inputs early
        missing = [i for i in inputs if i not in self.frames]
        if missing:
            raise ValueError(f"Target '{name}' references unknown inputs: {missing}. "
                             f"Available: {list(self.frames.keys())}")

        # Merge inputs
        per_table = {i: self.frames[i] for i in inputs}
        filtered = _apply_filters(per_table, pre_filter)
        merged = _merge_inputs(inputs, filtered, key)
        merged = _apply_merge_rules(merged, merge_rules, inputs)

        # Enrich (has access to both raw + compiled)
        enrich_steps = cfg.get("enrich") or []
        merged = _apply_enrich(merged, {**self.frames, **self.compiled}, enrich_steps)

        if post_filter:
            mask = build_mask(merged, post_filter)
            merged = merged[mask].copy()

        self.compiled[name] = merged
        return merged