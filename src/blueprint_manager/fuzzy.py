# fuzzy.py (fixed)
from __future__ import annotations
from typing import Dict, Tuple, List, Optional
import pandas as pd
from rapidfuzz import process, fuzz
from .textnorm import normalize

_SCORERS = {
    "ratio": fuzz.ratio,
    "partial_ratio": fuzz.partial_ratio,
    "token_sort_ratio": fuzz.token_sort_ratio,
    "token_set_ratio": fuzz.token_set_ratio,
}

def _block_key(s: str | None, mode: str) -> Optional[str]:
    if s is None:
        return None
    if mode == "first_char":
        return s[:1]
    if mode == "first2":
        return s[:2]
    return None  # "none"

def fuzzy_match_series(
    left: pd.Series,
    right_unique: pd.Series,
    *,
    normalize_steps: List[str],
    scorer: str,
    threshold: int,
    top_k: int,
    block: str = "first_char",
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Returns (match_to, match_score, match_method) aligned with left.index.
    match_to contains the ORIGINAL right value chosen (not normalized).
    match_method in {'exact','normalized','fuzzy','miss'}.
    """
    # 1) prep right side
    r_orig = right_unique.dropna().astype(str)
    r_norm = r_orig.map(lambda v: normalize(v, normalize_steps) or "")

    # map normalized -> original (first wins for determinism)
    norm_to_orig: Dict[str, str] = {}
    for normed, orig in zip(r_norm, r_orig):
        norm_to_orig.setdefault(normed, orig)

    # build candidate buckets keyed by block on NORMALIZED strings
    candidates_by_block: Dict[str, List[str]] = {}
    for normed in norm_to_orig.keys():
        b = _block_key(normed, block) or ""
        candidates_by_block.setdefault(b, []).append(normed)

    # scorer
    scorer_fn = _SCORERS.get(scorer, fuzz.token_sort_ratio)

    out_to = pd.Series(index=left.index, dtype=object)
    out_score = pd.Series(index=left.index, dtype="Int64")
    out_method = pd.Series(index=left.index, dtype=object)

    r_orig_set = set(r_orig.values)  # for fast exact-raw check
    all_norm_candidates = list(norm_to_orig.keys())

    for idx, raw in left.astype(object).items():
        if raw is None or (isinstance(raw, float) and pd.isna(raw)):
            out_method.at[idx] = "miss"
            continue

        s_raw = str(raw)
        s_norm = normalize(s_raw, normalize_steps) or ""

        # exact raw
        if s_raw in r_orig_set:
            out_to.at[idx] = s_raw
            out_score.at[idx] = 100
            out_method.at[idx] = "exact"
            continue

        # exact normalized
        if s_norm in norm_to_orig:
            out_to.at[idx] = norm_to_orig[s_norm]
            out_score.at[idx] = 100
            out_method.at[idx] = "normalized"
            continue

        # fuzzy: choose normalized candidates from the same block (or global fallback)
        block_key = _block_key(s_norm, block) or ""
        cands = candidates_by_block.get(block_key) or all_norm_candidates

        # IMPORTANT: pass score_cutoff so below-threshold returns None
        best = process.extractOne(
            s_norm,
            cands,
            scorer=scorer_fn,
            score_cutoff=threshold,
        )

        if best is None:
            out_method.at[idx] = "miss"
            continue

        best_norm, score, _ = best
        out_to.at[idx] = norm_to_orig[best_norm]       # map back to original value
        out_score.at[idx] = int(score)
        out_method.at[idx] = "fuzzy"

    return out_to, out_score, out_method
