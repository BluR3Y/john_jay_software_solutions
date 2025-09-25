# src/data_manager/enrich.py
from __future__ import annotations
from typing import Any, Dict, Iterable, Tuple
import pandas as pd
from pandas.api import types as ptypes
from rapidfuzz import process, fuzz

# ---------- helpers ----------

def _normalize_series(s: pd.Series, steps: Iterable[str]) -> pd.Series:
    out = s.astype("string")
    for st in steps:
        if st == "strip":
            out = out.str.strip()
        elif st == "lower":
            out = out.str.lower()
        elif st == "collapse_ws":
            out = out.str.replace(r"\s+", " ", regex=True)
        elif st == "strip_punct":
            out = out.str.replace(r"[^\w\s]", "", regex=True)
        # add more as needed
    return out

def _fuzzy_match_series(
    left: pd.Series,
    right: pd.Series,
    normalize_steps: Iterable[str],
    scorer: str = "token_sort_ratio",
    threshold: int = 90,
    top_k: int = 1,
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    lnorm = _normalize_series(left, normalize_steps).fillna("")
    rnorm = _normalize_series(right, normalize_steps).fillna("")

    # pick scorer
    scorer_fn = {
        "ratio": fuzz.ratio,
        "partial_ratio": fuzz.partial_ratio,
        "token_sort_ratio": fuzz.token_sort_ratio,
        "token_set_ratio": fuzz.token_set_ratio,
    }.get(scorer, fuzz.token_sort_ratio)

    # build a lookup from normalized right -> original right
    right_map = dict(zip(rnorm.tolist(), right.tolist()))

    # RapidFuzz needs choices; we use normalized right values
    choices = list(right_map.keys())

    matched_to = []
    matched_score = []
    for val in lnorm.tolist():
        if not val:
            matched_to.append(None)
            matched_score.append(0)
            continue
        # top-k then pick the best above threshold
        candidates = process.extract(val, choices, scorer=scorer_fn, limit=top_k)
        best = next((c for c in candidates if c[1] >= threshold), None)
        if best is None:
            matched_to.append(None)
            matched_score.append(0)
        else:
            matched_to.append(right_map.get(best[0]))
            matched_score.append(best[1])

    return (
        pd.Series(matched_to, index=left.index),
        pd.Series(matched_score, index=left.index),
        pd.Series(["fuzzy"] * len(left), index=left.index),
    )

# ---------- main enrich primitive ----------

def enrich_join(
    df: pd.DataFrame,
    dim: pd.DataFrame,
    *,
    left_on: str,
    right_on: str,
    add_map: Dict[str, str],
    how: str = "left",
    match: Dict[str, Any] | None = None,
) -> pd.DataFrame:
    """
    add_map: { new_col_name: source_col_in_dim }
    match: {
      "strategy": ["exact"] | ["exact","normalized","fuzzy"],
      "normalize": ["strip","lower","collapse_ws","strip_punct"],
      "fuzzy": {"scorer":"token_sort_ratio","threshold":90,"top_k":1},
      "audit": true|false,
      "on_miss": "leave_null" | "fail"
    }
    """
    match = match or {"strategy": ["exact"]}
    strategies = match.get("strategy", ["exact"])
    norm_steps = match.get("normalize", ["strip", "lower", "collapse_ws", "strip_punct"])

    # Always subset dim to the cols we need
    need_cols = {right_on} | set(add_map.values())
    dim = dim[[c for c in need_cols if c in dim.columns]].drop_duplicates(subset=[right_on])

    out = df.copy()

    # Strategy 1: Exact
    if strategies == ["exact"]:
        merged = out.merge(dim, how=how, left_on=left_on, right_on=right_on, suffixes=("", "_dim"))
        for new_col, src_col in add_map.items():
            if src_col in merged.columns:
                merged.rename(columns={src_col: new_col}, inplace=True)
        return merged.drop(columns=[right_on], errors="ignore")

    # Strategy 2/3: normalized / fuzzy
    # Build a candidate matched right key
    left_key = out[left_on].astype(object)
    right_key = dim[right_on].astype(object)

    # normalized exact first
    lnorm = _normalize_series(left_key, norm_steps)
    rnorm = _normalize_series(right_key, norm_steps)

    # fast path: normalized exact
    l2r_map = dict(zip(rnorm.tolist(), right_key.tolist()))
    normalized_match_to = lnorm.map(l2r_map)
    match_to = normalized_match_to.copy()
    match_score = pd.Series([100 if v is not None else 0 for v in match_to], index=out.index)
    match_method = pd.Series(["normalized" if v is not None else None for v in match_to], index=out.index)

    # fuzzy for the remaining nulls
    if "fuzzy" in strategies:
        need = match_to.isna()
        if need.any():
            f_to, f_score, _ = _fuzzy_match_series(
                left_key[need],
                right_key,
                normalize_steps=norm_steps,
                scorer=match.get("fuzzy", {}).get("scorer", "token_sort_ratio"),
                threshold=int(match.get("fuzzy", {}).get("threshold", 90)),
                top_k=int(match.get("fuzzy", {}).get("top_k", 1)),
            )
            match_to.loc[need] = f_to
            match_score.loc[need] = f_score
            match_method.loc[need] = "fuzzy"

    # Join on the resolved right key
    out["_match_key_tmp"] = match_to
    merged = out.merge(dim, how="left", left_on="_match_key_tmp", right_on=right_on, suffixes=("", "_dim"))
    merged.drop(columns=["_match_key_tmp", right_on], inplace=True, errors="ignore")

    # Rename mapped columns
    for new_col, src_col in add_map.items():
        if src_col in merged.columns:
            merged.rename(columns={src_col: new_col}, inplace=True)

    # Audit columns
    if match.get("audit"):
        base = left_on
        merged[f"{base}_match_to"] = match_to
        merged[f"{base}_match_score"] = match_score
        merged[f"{base}_match_method"] = match_method

    # on_miss policy
    if match.get("on_miss") == "fail":
        for new_col in add_map.keys():
            bad = merged[left_on].notna() & merged[new_col].isna()
            if bad.any():
                sample = merged.loc[bad, [left_on]].head(5).to_dict(orient="records")
                raise ValueError(f"Enrich join missed matches for {left_on}. Examples: {sample}")

    return merged
