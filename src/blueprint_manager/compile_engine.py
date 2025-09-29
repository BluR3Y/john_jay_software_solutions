# compile_engine.py
from __future__ import annotations
from typing import Any, Dict, List
import pandas as pd

from .filters import build_mask
from .plugins import ENRICH_PLUGINS
from .enrich import enrich_join  # your join primitive
from modules.script_logger import logger
log = logger.get_logger()

# ------------------------------
# Common helpers
# ------------------------------

def _apply_filters(per_table_frames: dict[str, pd.DataFrame], pre_filter_cfg: Dict[str, Any] | None) -> dict[str, pd.DataFrame]:
    if not pre_filter_cfg:
        return per_table_frames
    out: dict[str, pd.DataFrame] = {}
    for table_id, df in per_table_frames.items():
        expr = pre_filter_cfg.get(table_id)
        if expr:
            mask = build_mask(df, expr)
            kept = int(mask.sum())
            log.info(f"[pre_filter] {table_id}: kept {kept}/{len(df)} rows")
            out[table_id] = df[mask].copy()
        else:
            out[table_id] = df
    return out

def _merge_inputs(inputs: list[str], frames: dict[str, pd.DataFrame], key: list[str]) -> pd.DataFrame:
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
        # dict strategy first
        if isinstance(rule, dict):
            strat = rule.get("strategy")
            if strat == "first_non_null":
                priority = rule.get("priority") or []
                cols = [field] + [f"{field}__{inputs.index(src)}" for src in inputs if src in priority]
                cols = [c for c in cols if c in df.columns]
                if cols:
                    out[field] = df[cols].bfill(axis=1).iloc[:, 0]
            elif strat == "prefer_source":
                src = rule.get("prefer_source")
                cols = [field] + [c for c in df.columns if c.startswith(field + "__")]
                pick = next((c for c in cols if src and src in c), cols[0] if cols else None)
                if pick:
                    out[field] = df[pick]
            continue

        # string shorthands
        if isinstance(rule, str) and rule == "first_non_null":
            candidates = [c for c in df.columns if c.split("__")[0] == field]
            if candidates:
                out[field] = df[candidates].bfill(axis=1).iloc[:, 0]
            continue
    # drop suffixed columns
    keep = [c for c in out.columns if "__" not in c]
    return out[keep]

def _apply_enrich(df: pd.DataFrame, frames: dict[str, pd.DataFrame], steps: list[dict]) -> pd.DataFrame:
    out = df.copy()
    for idx, step in enumerate(steps or []):
        try:
            if "from" in step and "left_on" in step and "right_on" in step:
                src = step["from"]
                if src not in frames:
                    raise ValueError(f"Enrich source '{src}' not found. Available: {list(frames.keys())}")
                dim = frames[src]
                out = enrich_join(
                    out, dim,
                    left_on=step["left_on"],
                    right_on=step["right_on"],
                    add=step.get("add", {}),
                    how=step.get("how", "left"),
                    match=step.get("match"),
                )
            elif "fn" in step:
                fn = ENRICH_PLUGINS.get(step["fn"])
                if fn is None:
                    raise ValueError(f"Unknown enrich fn: {step['fn']}")
                out = fn(out, step.get("params", {}), frames=frames)
            else:
                raise ValueError(f"Invalid enrich step: {step}")
        except Exception as e:
            raise RuntimeError(f"[enrich step #{idx}] failed with error: {e}") from e
    return out

def _assert_columns(df: pd.DataFrame, required: List[str], table_id: str):
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"[union] Source '{table_id}' missing required columns {missing}")

def _coerce_dtypes(df: pd.DataFrame, schema_aliases: Dict[str, Any], columns: List[str]) -> pd.DataFrame:
    for col in columns:
        spec = (schema_aliases or {}).get(col) or {}
        t = spec.get("type")
        if not t:
            continue
        if t == "integer":
            df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")
        elif t in ("number", "float"):
            df[col] = pd.to_numeric(df[col], errors="coerce")
        elif t == "boolean":
            df[col] = df[col].astype("boolean")
        elif t == "date":
            df[col] = pd.to_datetime(df[col], errors="coerce")
        else:
            df[col] = df[col].astype("string")
    return df

# ------------------------------
# Union pipeline
# ------------------------------

def _compile_union(self, cfg: Dict[str, Any], pre_filtered_frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Execution order:
      validate inputs → columns/dtypes → concat → dedupe (optional) → enrich (optional) → post_filter (optional)
    """
    name     = cfg["name"]
    inputs   = cfg.get("inputs") or []
    columns  = cfg.get("columns")          # optional fixed ordering/subset
    add_src  = bool(cfg.get("add_source", False))
    dedupe   = cfg.get("dedupe_on")
    keep     = cfg.get("keep", "first")
    enrich_steps = cfg.get("enrich") or []
    post_f   = cfg.get("post_filter") or {}
    enrich_at = cfg.get("enrich_at", "post_dedupe")  # "post_dedupe" (default) | "pre_dedupe"

    # Validate inputs exist in the prefiltered dict
    missing_inputs = [i for i in inputs if i not in pre_filtered_frames]
    if missing_inputs:
        raise ValueError(f"[union] Target '{name}' references unknown inputs after pre_filter: {missing_inputs}. "
                         f"Available: {list(pre_filtered_frames.keys())}")

    # Determine column set (intersection if not provided)
    if columns is None:
        cols_sets = [set(pre_filtered_frames[i].columns) for i in inputs]
        columns = sorted(set.intersection(*cols_sets)) if cols_sets else []
        if not columns:
            raise ValueError(f"[union] No common columns across pre-filtered inputs {inputs}")

    # Select columns + dtype normalization + optional lineage
    pieces = []
    for src in inputs:
        df = pre_filtered_frames[src].copy()
        _assert_columns(df, columns, src)
        df = df.reindex(columns=columns)
        df = _coerce_dtypes(df, getattr(self, "schema_aliases", {}), columns)
        if add_src:
            df["_source"] = src
        pieces.append(df)
        log.info(f"[union] '{src}' contributes {len(df)} rows to '{name}'")

    out = pd.concat(pieces, ignore_index=True, sort=False)
    log.info(f"[union] '{name}' concatenated rows: {len(out)}")

    # Dedupe (optionally before enrich)
    if dedupe and enrich_at == "post_dedupe":
        before = len(out)
        out = out.drop_duplicates(subset=dedupe, keep=keep)
        log.info(f"[union] '{name}' dedup on {dedupe} keep={keep}: {before} → {len(out)}")
    
    # Enrich (has access to raw + compiled frames)
    if enrich_steps:
        out = _apply_enrich(out, {**self.frames, **self.compiled}, enrich_steps)

    # Dedupe after enrich if requested
    if dedupe and enrich_at == "pre_dedupe":
        before = len(out)
        out = out.drop_duplicates(subset=dedupe, keep=keep)
        log.info(f"[union] '{name}' dedup (post-enrich) on {dedupe} keep={keep}: {before} → {len(out)}")

    # Post-filter on final frame
    if post_f:
        mask = build_mask(out, post_f)
        kept = int(mask.sum())
        out = out[mask].copy()
        log.info(f"[union] '{name}' post_filter kept {kept}/{len(mask)} rows")

    return out

# ------------------------------
# Merge pipeline
# ------------------------------

def _compile_merge(self, cfg: Dict[str, Any], pre_filtered_frames: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    name = cfg.get("name")
    inputs = cfg.get("inputs") or []
    key = cfg.get("key") or []
    merge_rules = cfg.get("merge_rules") or {}
    enrich_steps = cfg.get("enrich") or []
    post_f = cfg.get("post_filter") or {}

    merged = _merge_inputs(inputs, pre_filtered_frames, key)
    merged = _apply_merge_rules(merged, merge_rules, inputs)

    if enrich_steps:
        merged = _apply_enrich(merged, {**self.frames, **self.compiled}, enrich_steps)

    if post_f:
        mask = build_mask(merged, post_f)
        merged = merged[mask].copy()
    
    return merged

# ------------------------------
# Diffs pipeline
# ------------------------------

def _validate_keys(df: pd.DataFrame, keys: List[str], name: str):
    missing = [k for k in keys if k not in df.columns]
    if missing:
        raise ValueError(f"[diff] '{name}' missing key columns {missing}")

def _compile_diff(self, cfg: Dict[str, Any], pre_filtered_frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    name    = cfg["name"]
    left_id = cfg["left"]
    right_id= cfg["right"]
    keys    = cfg.get("on") or []
    side    = cfg.get("side", "left_only")  # left_only|right_only|symmetric_diff|both
    project = cfg.get("project", None)      # left|right|both|keys (auto if None)
    post_f  = cfg.get("post_filter") or {}
    add_src = bool(cfg.get("add_source", side == "symmetric_diff"))
    columns_left  = cfg.get("columns_left")    # optional projection for left non-key cols
    columns_right = cfg.get("columns_right")   # optional projection for right non-key cols

    # Validate presence
    if left_id not in pre_filtered_frames or right_id not in pre_filtered_frames:
        raise ValueError(f"[diff] Missing inputs after pre_filter. "
                         f"Available: {list(pre_filtered_frames.keys())}")
    left  = pre_filtered_frames[left_id].copy()
    right = pre_filtered_frames[right_id].copy()

    if not keys:
        raise ValueError(f"[diff] '{name}' requires 'on' key columns")

    _validate_keys(left,  keys, left_id)
    _validate_keys(right, keys, right_id)

    # Optional column projection before merge (keeps keys + selected non-keys)
    if columns_left is not None:
        left = left[keys + [c for c in columns_left if c not in keys]]
    if columns_right is not None:
        right = right[keys + [c for c in columns_right if c not in keys]]

    # Outer merge with indicator
    merged = left.merge(
        right,
        how="outer",
        on=keys,
        suffixes=("_left", "_right"),
        indicator=True,
    )

    # Side selection
    if side == "left_only":
        out = merged[merged["_merge"] == "left_only"].copy()
    elif side == "right_only":
        out = merged[merged["_merge"] == "right_only"].copy()
    elif side == "symmetric_diff":
        out = merged[merged["_merge"] != "both"].copy()
    elif side == "both":
        out = merged[merged["_merge"] == "both"].copy()
    else:
        raise ValueError(f"[diff] Invalid 'side': {side}")

    log.info(f"[diff] '{name}' side={side}: {len(out)} rows")

    # Decide projection default if not specified
    if project is None:
        project = (
            "left" if side == "left_only" else
            "right" if side == "right_only" else
            "both"  # for symmetric_diff/both keep both sides by default
        )

    # Build final columns
    key_cols = list(keys)
    if project == "keys":
        final_cols = key_cols
        out = out[final_cols + (["_merge"] if side in ("both", "symmetric_diff") else [])].copy()

    elif project == "left":
        left_cols_sfx = [c for c in out.columns if c.endswith("_left")]
        # 1) subset with suffixed names
        select_cols = key_cols + left_cols_sfx + (["_merge"] if side in ("both", "symmetric_diff") else [])
        out = out[select_cols].copy()
        # 2) rename to unsuffixed
        out.rename(columns={c: c[:-5] for c in left_cols_sfx}, inplace=True)
        # 3) rebuild final_cols with unsuffixed names
        final_cols = key_cols + [c[:-5] for c in left_cols_sfx]

    elif project == "right":
        right_cols_sfx = [c for c in out.columns if c.endswith("_right")]
        select_cols = key_cols + right_cols_sfx + (["_merge"] if side in ("both", "symmetric_diff") else [])
        out = out[select_cols].copy()
        out.rename(columns={c: c[:-6] for c in right_cols_sfx}, inplace=True)
        final_cols = key_cols + [c[:-6] for c in right_cols_sfx]

    elif project == "both":
        # keep both sides with suffixes (and _merge if desired)
        left_cols_sfx  = [c for c in out.columns if c.endswith("_left")]
        right_cols_sfx = [c for c in out.columns if c.endswith("_right")]
        final_cols = key_cols + left_cols_sfx + right_cols_sfx
        out = out[final_cols + (["_merge"] if True else [])].copy()  # keep _merge for 'both'

    else:
        raise ValueError(f"[diff] Invalid 'project': {project}")

    # Add lineage if requested (only meaningful for symmetric_diff)
    if add_src:
        def src_from_merge(m):
            if m == "left_only": return "left"
            if m == "right_only": return "right"
            return "both"
        out["_source"] = out["_merge"].map(src_from_merge)
        final_cols = final_cols + ["_source"]

    # Post-filter on the projected view
    out = out[final_cols + (["_merge"] if project == "both" else [])].copy()
    if post_f:
        mask = build_mask(out, post_f)
        out = out[mask].copy()
        log.info(f"[diff] '{name}' post_filter kept {len(out)} rows after filter")

    return out


# ------------------------------
# Compiler
# ------------------------------

class Compiler:
    def __init__(self, frames: dict[str, pd.DataFrame], schema_aliases: Dict[str, Any] | None = None):
        self.frames = frames              # raw source frames
        self.compiled: dict[str, pd.DataFrame] = {}
        self.schema_aliases = schema_aliases or {}

    def compile_target(self, cfg: Dict[str, Any]) -> pd.DataFrame:
        name   = cfg.get("name")
        inputs = cfg.get("inputs") or []
        mode   = cfg.get("mode", "merge")
        pre_f  = cfg.get("pre_filter") or {}

        log.info(f"Compiling target: {name}")

        # Validate inputs upfront (exist in self.frames)
        missing = [i for i in inputs if i not in self.frames]
        if missing:
            raise ValueError(f"Target '{name}' references unknown inputs: {missing}. "
                             f"Available: {list(self.frames.keys())}")

        # Apply pre-filter per input
        per_table = {i: self.frames[i] for i in inputs}
        pre_filtered = _apply_filters(per_table, pre_f)

        # Route by mode
        if mode == "union":
            out = _compile_union(self, cfg, pre_filtered)
        elif mode == "diff":
            out = _compile_diff(self, cfg, pre_filtered)
        else:
            out = _compile_merge(self, cfg, pre_filtered)
        # Save for downstream enrich steps in later targets
        
        self.compiled[name] = out
        return out