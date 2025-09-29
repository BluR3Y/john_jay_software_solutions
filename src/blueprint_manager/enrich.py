# blueprint_manager/enrich.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Tuple, TypedDict, Union
import logging
import re
import unicodedata

import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz

log = logging.getLogger(__name__)

# -------------------- Typed config & constants --------------------

How = Literal["left", "inner"]
Strategy = Literal["exact", "normalized", "fuzzy"]
OnConflict = Literal["error", "skip", "overwrite", "suffix"]
RightKeep = Literal["first", "last"]
WritePolicy = Literal["fillna", "overwrite"]
Cardinality = Literal["m:1", "1:1"]
OnMiss = Literal["leave_null", "fail"]

class FuzzyCfg(TypedDict, total=False):
    scorer: Literal["ratio", "partial_ratio", "token_sort_ratio", "token_set_ratio"]
    threshold: int        # 0..100, default 90
    top_k: int            # default 1
    max_bucket: int       # cap candidates per bucket (default 5000)
    use_all_if_empty_bucket: bool  # default True (only if right small)

class MatchCfg(TypedDict, total=False):
    strategy: List[Strategy]     # default ["exact"]
    normalize: List[str]         # "strip","lower","upper","collapse_ws","strip_punct","nfkc","strip_accents"
    fuzzy: FuzzyCfg
    left_kind:  Literal["string","integer","number","date"]
    right_kind: Literal["string","integer","number","date"]
    cardinality: Cardinality     # default "m:1"
    min_len: int                 # default 2
    right_keep: RightKeep        # default "first"
    on_miss: OnMiss              # default "leave_null"
    write_policy: WritePolicy    # default "fillna"

_SCORERS = {
    "ratio": fuzz.ratio,
    "partial_ratio": fuzz.partial_ratio,
    "token_sort_ratio": fuzz.token_sort_ratio,
    "token_set_ratio": fuzz.token_set_ratio,
}

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_WS_RE = re.compile(r"\s+")

# -------------------- Normalization helpers --------------------

def _to_str_series(s: pd.Series) -> pd.Series:
    return s.astype("string")

def _normalize_series(s: pd.Series, steps: Iterable[str]) -> pd.Series:
    """
    Deterministic normalization pipeline.
    Steps: strip, lower, upper, collapse_ws, strip_punct, nfkc, strip_accents
    """
    s = _to_str_series(s)
    steps_norm = [step.strip().lower() for step in steps]
    out = s.copy()

    def _to_na(x):
        return pd.NA if x is None else x

    if "nfkc" in steps_norm:
        out = out.map(lambda x: pd.NA if x is pd.NA else unicodedata.normalize("NFKC", x))
    if "strip_accents" in steps_norm:
        def deaccent(u: str) -> str:
            norm = unicodedata.normalize("NFD", u)
            return "".join(ch for ch in norm if unicodedata.category(ch) != "Mn")
        out = out.map(lambda x: pd.NA if x is pd.NA else deaccent(x))
    if "strip_punct" in steps_norm:
        out = out.map(lambda x: pd.NA if x is pd.NA else _PUNCT_RE.sub(" ", x))
    if "collapse_ws" in steps_norm:
        out = out.map(lambda x: pd.NA if x is pd.NA else _WS_RE.sub(" ", x))
    if "strip" in steps_norm:
        out = out.map(lambda x: pd.NA if x is pd.NA else x.strip())
    if "lower" in steps_norm and "upper" in steps_norm:
        steps_norm.remove("upper")
    if "lower" in steps_norm:
        out = out.str.lower()
    elif "upper" in steps_norm:
        out = out.str.upper()

    return out.astype("string").map(_to_na)

# -------------------- Matching helpers --------------------

def _hash_index(series: pd.Series) -> Dict[str, List[int]]:
    """Build dict key -> list of row positions; skips nulls."""
    idx: Dict[str, List[int]] = {}
    arr = series.array
    for i, v in enumerate(arr):
        if v is not None and v is not pd.NA:
            idx.setdefault(v, []).append(i)
    return idx

def _stage_exact_norm(
    lkeys: pd.Series, rkeys: pd.Series, strategy_label: Strategy
) -> pd.DataFrame:
    """
    Return rows: [left_idx, right_idx, strategy, score] for exact/normalized (score=100).
    Requires lkeys/rkeys to be strings.
    """
    r_index = _hash_index(rkeys)
    rows: List[Tuple[int, int, str, int]] = []
    for li, lk in enumerate(lkeys.array):
        if lk is None or lk is pd.NA:
            continue
        for rpos in r_index.get(lk, []):
            rows.append((li, rpos, strategy_label, 100))
    return pd.DataFrame(rows, columns=["left_idx", "right_idx", "strategy", "score"])

def _bucket_key(s: Optional[str]) -> Optional[str]:
    if s is None or s is pd.NA:
        return None
    s = s.strip()
    return s[:1] if s else None

def _stage_fuzzy(
    lnorm: pd.Series,
    rnorm: pd.Series,
    fuzzy_cfg: FuzzyCfg,
    left_unmatched_mask: np.ndarray,
    min_len: int,
) -> pd.DataFrame:
    """
    Fuzzy match remaining left rows against right rows using first-char buckets (with caps).
    Returns columns [left_idx,right_idx,strategy,score].
    """
    scorer_name = fuzzy_cfg.get("scorer", "token_set_ratio")
    threshold = int(fuzzy_cfg.get("threshold", 90))
    top_k = int(fuzzy_cfg.get("top_k", 1))
    max_bucket = int(fuzzy_cfg.get("max_bucket", 5000))
    use_all_if_empty_bucket = bool(fuzzy_cfg.get("use_all_if_empty_bucket", True))
    if scorer_name not in _SCORERS:
        raise ValueError(f"Unsupported fuzzy.scorer={scorer_name}")
    if not (0 <= threshold <= 100):
        raise ValueError("fuzzy.threshold must be between 0 and 100")

    scorer = _SCORERS[scorer_name]

    # Right buckets by first char
    buckets: Dict[str, List[Tuple[int, str]]] = {}
    for ri, rv in enumerate(rnorm.array):
        if rv is None or rv is pd.NA:
            continue
        b = _bucket_key(rv)
        if b is None:
            continue
        buckets.setdefault(b, []).append((ri, rv))

    rows: List[Tuple[int, int, str, int]] = []
    left_positions = np.where(left_unmatched_mask)[0]

    for li in left_positions:
        lv = lnorm.iat[li]
        if lv is None or lv is pd.NA:
            continue
        if len(lv.strip()) < max(2, min_len):
            continue

        b = _bucket_key(lv)
        candidates = buckets.get(b or "", [])

        if (not candidates) and use_all_if_empty_bucket and len(rnorm) <= 2000:
            candidates = [(ri, rv) for ri, rv in enumerate(rnorm.array) if rv is not None and rv is not pd.NA]

        if not candidates:
            continue

        if len(candidates) > max_bucket:
            # Skip pathological buckets to protect runtime
            log.debug("fuzzy bucket too large (%d) for left idx %d; skipping", len(candidates), li)
            continue

        strings = [rv for (_, rv) in candidates]
        matches = process.extract(lv, strings, scorer=scorer, limit=top_k)
        for match_str, score, idx in matches:
            if score >= threshold:
                rpos = candidates[idx][0]
                rows.append((li, rpos, "fuzzy", int(score)))

    if rows:
        return pd.DataFrame(rows, columns=["left_idx", "right_idx", "strategy", "score"])
    else:
        return pd.DataFrame(columns=["left_idx", "right_idx", "strategy", "score"], dtype=object)

def _choose_best_match(matches: pd.DataFrame) -> Tuple[pd.Series, pd.DataFrame]:
    """
    Given stacked candidates across stages, return:
      - links: pd.Series indexed by left_idx with chosen right_idx (nullable Int64)
      - audit_best: per-left best row (keeps strategy and score)
    Deterministic order: strategy exact < normalized < fuzzy, then score desc, then right_idx asc.
    """
    if matches.empty:
        links = pd.Series(pd.array([pd.NA] * 0, dtype="Int64"), index=pd.Index([], name="left_idx"))
        return links, matches

    strategy_rank = {"exact": 0, "normalized": 1, "fuzzy": 2}
    matches = matches.copy()
    matches["__rank"] = matches["strategy"].map(strategy_rank).astype(int)
    matches = matches.sort_values(["left_idx", "__rank", "score", "right_idx"],
                                  ascending=[True, True, False, True])
    audit_best = matches.drop_duplicates("left_idx", keep="first")
    links = audit_best.set_index("left_idx")["right_idx"].astype("Int64")
    return links, audit_best[["left_idx", "right_idx", "strategy", "score"]]

def _coerce_kind(series: pd.Series, kind: str, for_text_ops: bool) -> pd.Series:
    """
    Coerce to appropriate dtype for matching.
    for_text_ops=True → we will string-ify regardless (needed for normalized/fuzzy)
    """
    kind = (kind or "string").lower()
    if for_text_ops:
        return _to_str_series(series)
    if kind in ("integer", "number"):
        return pd.to_numeric(series, errors="coerce")
    if kind == "date":
        return pd.to_datetime(series, errors="coerce")
    return _to_str_series(series)

def _assert_cardinality(right_keys: pd.Series, cardinality: Cardinality):
    if cardinality == "1:1":
        counts = right_keys.value_counts(dropna=True)
        dups = counts[counts > 1]
        if not dups.empty:
            raise ValueError(
                f"enrich.cardinality=1:1 but right side has duplicate keys for {len(dups)} distinct values. "
                f"Example keys: {list(map(str, dups.index[:3]))}"
            )

def _nullable_int_dtype(dtype: Any) -> Any:
    # Normalize int dtypes to pandas nullable Int64
    if pd.api.types.is_integer_dtype(dtype):
        return "Int64"
    return dtype

# --------------------------- Main API --------------------------------

def enrich_join(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    left_on: str,
    right_on: str,
    add: Mapping[str, str],
    how: How = "left",
    match: Optional[MatchCfg] = None,
    on_conflict: OnConflict = "error",
    return_audit: bool = False,
) -> Union[pd.DataFrame, Tuple[pd.DataFrame, pd.DataFrame]]:
    """
    Multi-strategy enrichment: exact → normalized → fuzzy, with single final materialization.

    Parameters
    ----------
    left, right : DataFrames
    left_on, right_on : column names to match on
    add : mapping of {output_col_in_left: source_col_in_right}
    how : "left" | "inner"
    match : MatchCfg (see above). Defaults:
        strategy=["exact"], normalize=["strip","collapse_ws","strip_punct","nfkc","strip_accents","lower"],
        fuzzy={"scorer":"token_set_ratio","threshold":90,"top_k":1,"max_bucket":5000,"use_all_if_empty_bucket":True},
        left_kind="string", right_kind="string", cardinality="m:1", min_len=2,
        right_keep="first", on_miss="leave_null", write_policy="fillna"
    on_conflict : "error" (default), "skip", "overwrite", "suffix"
    return_audit : if True, return (enriched_df, audit_df)
    """
    cfg: MatchCfg = {
        "strategy": ["exact"],
        "normalize": ["strip", "collapse_ws", "strip_punct", "nfkc", "strip_accents", "lower"],
        "fuzzy": {"scorer": "token_set_ratio", "threshold": 90, "top_k": 1, "max_bucket": 5000, "use_all_if_empty_bucket": True},
        "left_kind": "string",
        "right_kind": "string",
        "cardinality": "m:1",
        "min_len": 2,
        "right_keep": "first",
        "on_miss": "leave_null",
        "write_policy": "fillna",
        **(match or {}),
    }

    strategy = [s.lower() for s in cfg.get("strategy", ["exact"])]
    norm_steps = cfg.get("normalize", [])
    fuzzy_cfg = cfg.get("fuzzy", {}) or {}
    left_kind = (cfg.get("left_kind") or "string").lower()
    right_kind = (cfg.get("right_kind") or "string").lower()
    cardinality = (cfg.get("cardinality") or "m:1").lower()  # type: ignore
    min_len = max(2, int(cfg.get("min_len", 2)))
    right_keep = (cfg.get("right_keep") or "first").lower()  # type: ignore
    on_miss = (cfg.get("on_miss") or "leave_null").lower()   # type: ignore
    write_policy = (cfg.get("write_policy") or "fillna").lower()  # type: ignore

    if how not in ("left", "inner"):
        raise ValueError(f"Unsupported how={how}")
    if on_conflict not in ("error", "skip", "overwrite", "suffix"):
        raise ValueError(f"Unsupported on_conflict={on_conflict}")
    if right_keep not in ("first", "last"):
        raise ValueError(f"Unsupported right_keep={right_keep}")
    if write_policy not in ("fillna", "overwrite"):
        raise ValueError(f"Unsupported write_policy={write_policy}")
    if left_on not in left.columns:
        raise ValueError(f"Left key '{left_on}' not found")
    if right_on not in right.columns:
        raise ValueError(f"Right key '{right_on}' not found")
    need_right = {right_on} | set(add.values())
    miss_right_cols = [c for c in need_right if c not in right.columns]
    if miss_right_cols:
        raise ValueError(f"Right table missing required columns: {miss_right_cols}")

    # Defensive copy & positional indices
    left = left.reset_index(drop=True)
    right = right.reset_index(drop=True)

    # Coerce keys
    text_ops = ("normalized" in strategy) or ("fuzzy" in strategy)
    left_key_exact = _coerce_kind(left[left_on], left_kind, for_text_ops=text_ops)
    right_key_exact = _coerce_kind(right[right_on], right_kind, for_text_ops=text_ops)

    # Normalized keys if needed
    left_key_norm = _normalize_series(left_key_exact, norm_steps) if text_ops else None
    right_key_norm = _normalize_series(right_key_exact, norm_steps) if text_ops else None

    # Right-side de-dup if requested (deterministic keep)
    if right_keep in ("first", "last"):
        # choose normalized key if available, else stringified exact
        rkey = right_key_norm if right_key_norm is not None else right_key_exact.astype("string")
        # mark first/last occurrence per key (excluding NAs)
        mask = rkey.notna()
        # pandas keeps first/last by default in drop_duplicates; we just compute indices
        dedup = pd.Series(True, index=right.index)
        dup_idx = rkey[mask].duplicated(keep=right_keep)
        dedup.loc[dup_idx.index[dup_idx]] = False
        right = right.loc[dedup].reset_index(drop=True)
        right_key_exact = right_key_exact.loc[dedup].reset_index(drop=True)
        if right_key_norm is not None:
            right_key_norm = right_key_norm.loc[dedup].reset_index(drop=True)

    # Cardinality check
    if cardinality == "1:1":
        key_for_check = right_key_norm if right_key_norm is not None else right_key_exact.astype("string")
        _assert_cardinality(key_for_check, "1:1")

    # --------- Stage candidates
    candidates: List[pd.DataFrame] = []

    # Exact: prefer true exact semantics when no text ops are requested; else compare as strings
    if "exact" in strategy:
        if text_ops:
            lex = left_key_exact.astype("string")
            rex = right_key_exact.astype("string")
        else:
            # For numeric/date, stringify for the hasher but keep equality exactness
            lex = left_key_exact.astype("string")
            rex = right_key_exact.astype("string")
        candidates.append(_stage_exact_norm(lex, rex, "exact"))

    if "normalized" in strategy:
        assert left_key_norm is not None and right_key_norm is not None
        candidates.append(_stage_exact_norm(left_key_norm, right_key_norm, "normalized"))

    # Build unmatched mask before fuzzy
    if candidates:
        stacked = pd.concat(candidates, ignore_index=True) if len(candidates) > 1 else candidates[0]
        matched_left = stacked["left_idx"].unique()
        unmatched_mask = np.ones(len(left), dtype=bool)
        unmatched_mask[matched_left] = False
    else:
        unmatched_mask = np.ones(len(left), dtype=bool)

    if "fuzzy" in strategy:
        assert left_key_norm is not None and right_key_norm is not None
        candidates.append(_stage_fuzzy(left_key_norm, right_key_norm, fuzzy_cfg, unmatched_mask, min_len))

    # Final candidate stack
    all_matches = (
        pd.concat(candidates, ignore_index=True)
        if candidates else pd.DataFrame(columns=["left_idx","right_idx","strategy","score"], dtype=object)
    )

    # Choose best per-left deterministically
    links, audit_best = _choose_best_match(all_matches)

    # Align links to all left rows
    full_index = pd.RangeIndex(len(left))
    links = links.reindex(full_index, fill_value=pd.NA).astype("Int64")
    matched_mask = links.notna()

    # Materialize
    out = left.copy()
    if how == "inner":
        keep_idx = links.index[matched_mask].to_numpy()
        out = out.loc[keep_idx].reset_index(drop=True)
        links = links.loc[keep_idx].reset_index(drop=True)
        matched_mask = links.notna()

    # Write outputs with dtype preservation and write_policy
    for out_col, src_col in add.items():
        # Conflict policy on existing columns
        target_name = out_col
        if target_name in out.columns:
            if on_conflict == "error":
                raise ValueError(f"enrich.add target column '{out_col}' already exists (on_conflict=error)")
            elif on_conflict == "skip":
                log.info("enrich.add target '%s' exists; skipping (on_conflict=skip)", out_col)
                continue
            elif on_conflict == "suffix":
                base = target_name
                k = 1
                while (new_name := f"{base}_r{k}") in out.columns:
                    k += 1
                log.info("enrich.add target '%s' exists; writing to '%s' (on_conflict=suffix)", out_col, new_name)
                target_name = new_name
            elif on_conflict == "overwrite":
                pass

        # Initialize with NA using right dtype (nullable ints normalized)
        r_dtype = _nullable_int_dtype(right[src_col].dtype)
        out[target_name] = pd.Series([pd.NA] * len(out), dtype=r_dtype)

        mask = matched_mask.to_numpy()
        if not mask.any():
            continue

        right_pos = links[mask].astype(int).to_numpy()
        values = right.iloc[right_pos][src_col].to_numpy()

        if write_policy == "fillna" and out_col in out.columns:
            # only fill nulls in existing column
            tgt = out[out_col]
            fill_mask = mask & tgt.isna().to_numpy()
            if fill_mask.any():
                out.loc[fill_mask, out_col] = values[fill_mask[mask]]
        else:
            out.loc[mask, target_name] = values

    # on_miss policy (non-null, non-empty left keys that remained unmatched)
    if on_miss == "fail" and how == "left":
        left_key_raw = left[left_on].astype("string")
        bad = left_key_raw.notna() & ~left_key_raw.str.strip().eq("") & ~matched_mask
        if bad.any():
            sample = left.loc[bad, [left_on]].head(10).to_dict(orient="records")
            raise ValueError(f"enrich_join: no match for some '{left_on}' rows. Examples: {sample}")

    if return_audit:
        audit = audit_best.copy()
        if not audit.empty:
            audit["left_key_raw"] = left[left_on].take(audit["left_idx"]).astype("string").to_numpy()
            audit["right_key_raw"] = right[right_on].take(audit["right_idx"]).astype("string").to_numpy()
        return out, audit.reset_index(drop=True)

    return out
