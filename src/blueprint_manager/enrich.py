# src/data_manager/enrich.py
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Literal, Mapping, Optional, Tuple, TypedDict, Union
import unicodedata

import pandas as pd
from rapidfuzz import process, fuzz


# ------------------------------- Types ---------------------------------------

How = Literal["left", "inner"]
Strategy = Literal["exact", "normalized", "fuzzy"]

class FuzzyCfg(TypedDict, total=False):
    scorer: Literal["ratio", "partial_ratio", "token_sort_ratio", "token_set_ratio"]
    threshold: int        # default 90
    top_k: int            # default 1

class MatchCfg(TypedDict, total=False):
    strategy: List[Strategy]     # default ["exact"]
    normalize: List[str]         # steps: "strip","lower","upper","collapse_ws","strip_punct","nfkc","strip_accents"
    fuzzy: FuzzyCfg
    left_kind:  Literal["string","integer","number","date"]
    right_kind: Literal["string","integer","number","date"]
    right_keep: Literal["first","last"]   # default "first"
    audit: bool                           # default False
    on_miss: Literal["leave_null","fail"] # default "leave_null"


# ----------------------------- Public API ------------------------------------

def enrich_join(
    df: pd.DataFrame,
    dim: pd.DataFrame,
    *,
    left_on: str,
    right_on: str,
    add_map: Dict[str, str] | None = None,   # { NEW_NAME -> SRC_NAME_IN_RIGHT }
    how: How = "left",
    match: MatchCfg | None = None,
) -> pd.DataFrame:
    """
    Robust join-based enrichment with staged matching and deferred renaming.

    Parameters
    ----------
    df : pd.DataFrame
        Left (working) DataFrame.
    dim : pd.DataFrame
        Right (dimension/lookup) DataFrame.
    left_on, right_on : str
        Join key column names on left/right.
    add_map : dict[str, str], optional
        Mapping of NEW output column name -> SOURCE column name from `dim`.
        Example: { "org_id": "ext_org_id", "org_type": "org_type" }.
    how : {"left","inner"}, default "left"
        Join type; for "inner", filtering is deferred until after all stages.
    match : dict, optional
        {
          "strategy": ["exact"] | ["exact","normalized"] | ["exact","normalized","fuzzy"],
          "normalize": ["strip","lower","collapse_ws","strip_punct","nfkc","strip_accents"],
          "fuzzy": {"scorer":"token_sort_ratio","threshold":90,"top_k":1},
          "left_kind":  "string|integer|number|date",
          "right_kind": "string|integer|number|date",
          "right_keep": "first|last",
          "audit": true|false,
          "on_miss": "leave_null"|"fail"
        }

    Returns
    -------
    pd.DataFrame
        Enriched DataFrame with added/renamed columns. Row order is preserved.
    """

    add_map = add_map or {}
    m = match or {}
    strategies: List[Strategy] = list(m.get("strategy", ["exact"]))  # type: ignore[list-item]
    norm_steps: Iterable[str] = m.get("normalize", ["strip", "lower", "collapse_ws", "strip_punct"])
    left_kind: Optional[str]  = m.get("left_kind")
    right_kind: Optional[str] = m.get("right_kind")
    right_keep: str           = m.get("right_keep", "first")  # "first" | "last"
    audit: bool               = bool(m.get("audit", False))
    on_miss: str              = m.get("on_miss", "leave_null")

    # ---------------- validations ----------------
    if how not in {"left", "inner"}:
        raise ValueError(f"[enrich] unsupported how='{how}' (allowed: 'left','inner')")
    if right_keep not in {"first", "last"}:
        raise ValueError(f"[enrich] unsupported right_keep='{right_keep}' (allowed: 'first','last')")
    if left_on not in df.columns:
        raise ValueError(f"[enrich] left key '{left_on}' not found in left columns")
    if right_on not in dim.columns:
        raise ValueError(f"[enrich] right key '{right_on}' not found in right columns")

    needed_right = {right_on} | set(add_map.values())
    missing = [c for c in needed_right if c not in dim.columns]
    if missing:
        raise ValueError(f"[enrich] right table missing columns required by add_map: {missing}")

    # ---------------- helpers ----------------
    def _coerce_for_join(series: pd.Series, kind: Optional[str]) -> pd.Series:
        if kind == "integer": return pd.to_numeric(series, errors="coerce").astype("Int64")
        if kind == "number":  return pd.to_numeric(series, errors="coerce")
        if kind == "date":    return pd.to_datetime(series, errors="coerce")
        if kind == "string":  return series.astype("string")
        return series

    def _strip_accents(text: str) -> str:
        # Normalize to NFD and remove combining marks
        return "".join(ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch))

    def _normalize_series(s: pd.Series, steps: Iterable[str]) -> pd.Series:
        out = s.astype("string")
        for st in steps:
            if st == "nfkc":
                out = out.apply(lambda x: unicodedata.normalize("NFKC", x) if pd.notna(x) else x)
            elif st == "strip_accents":
                out = out.apply(lambda x: _strip_accents(x) if pd.notna(x) else x)
            elif st == "strip":
                out = out.str.strip()
            elif st == "lower":
                out = out.str.lower()
            elif st == "upper":
                out = out.str.upper()
            elif st == "collapse_ws":
                out = out.str.replace(r"\s+", " ", regex=True)
            elif st == "strip_punct":
                out = out.str.replace(r"[^\w\s]", "", regex=True)
        return out

    def _ensure_unique_right(df_right: pd.DataFrame, key: str) -> pd.DataFrame:
        r = df_right[df_right[key].notna()].copy()
        if r.duplicated(subset=[key]).any():
            r = r.drop_duplicates(subset=[key], keep=right_keep)  # type: ignore[arg-type]
        return r

    def _resolve_src_col(M: pd.DataFrame, src: str) -> Optional[str]:
        """Return the column name in M that contains the right-side source field (handles suffix)."""
        if src in M.columns:
            return src
        alt = f"{src}_dim"
        if alt in M.columns:
            return alt
        return None

    def _miss_mask(M: Optional[pd.DataFrame], left_index: pd.Index) -> pd.Series:
        """Return boolean Series of rows that still need enrichment (True = missing)."""
        if M is None:
            return pd.Series(True, index=left_index)
        if add_map:
            # look for any of the source (or suffixed) columns being present and non-null
            present_cols: List[str] = []
            for src in add_map.values():
                col = _resolve_src_col(M, src)
                if col:
                    present_cols.append(col)
            if present_cols:
                # rows are 'miss' if ALL present sources are NA
                return M[present_cols].isna().all(axis=1)
            # fallback if nothing present yet (shouldn't happen)
            return pd.Series(True, index=M.index)
        # if no add_map, use right key presence as proxy
        if right_on in M.columns:
            return M[right_on].isna()
        return pd.Series(True, index=M.index)

    def _prepare_audit_cols(M: pd.DataFrame) -> None:
        for col, dtype in [(f"{left_on}_match_to", object),
                           (f"{left_on}_match_score", "Int64"),
                           (f"{left_on}_match_method", object)]:
            if col not in M.columns:
                M[col] = pd.Series(index=M.index, dtype=dtype)

    def _fuzzy_match_series(
        left_vals: pd.Series,
        right_vals: pd.Series,
        normalize_steps: Iterable[str],
        scorer_name: str = "token_sort_ratio",
        threshold: int = 90,
        top_k: int = 1,
    ) -> Tuple[pd.Series, pd.Series]:
        lnorm = _normalize_series(left_vals, normalize_steps).fillna("")
        rnorm = _normalize_series(right_vals, normalize_steps).fillna("")

        scorer_fn = {
            "ratio": fuzz.ratio,
            "partial_ratio": fuzz.partial_ratio,
            "token_sort_ratio": fuzz.token_sort_ratio,
            "token_set_ratio": fuzz.token_set_ratio,
        }.get(scorer_name, fuzz.token_sort_ratio)

        # De-duplicate normalized right values before building the lookup (honor right_keep)
        rnorm_df = pd.DataFrame({"_norm": rnorm, "_orig": right_vals})
        rnorm_df = rnorm_df.dropna(subset=["_norm"])
        rnorm_df = rnorm_df.drop_duplicates(subset=["_norm"], keep=right_keep)  # type: ignore[arg-type]
        rmap = dict(zip(rnorm_df["_norm"].tolist(), rnorm_df["_orig"].tolist()))
        choices = list(rmap.keys())

        matched_to: list[Any] = []
        matched_score: list[int] = []
        for val in lnorm.tolist():
            if not val:
                matched_to.append(None); matched_score.append(0); continue
            candidates = process.extract(val, choices, scorer=scorer_fn, limit=top_k)
            best = next((c for c in candidates if int(c[1]) >= threshold), None)
            if best is None:
                matched_to.append(None); matched_score.append(0)
            else:
                matched_to.append(rmap.get(best[0])); matched_score.append(int(best[1]))
        return pd.Series(matched_to, index=left_vals.index), pd.Series(matched_score, index=left_vals.index)

    # ---------------- prep ----------------
    left  = df.copy()
    left["_ord__"] = range(len(left))  # preserve order
    right = dim[list(needed_right)].copy()

    if left_kind:
        left[left_on] = _coerce_for_join(left[left_on], left_kind)
    if right_kind:
        right[right_on] = _coerce_for_join(right[right_on], right_kind)

    merged: Optional[pd.DataFrame] = None

    # ---------------- stage 1: exact ----------------
    if "exact" in strategies:
        r_exact = _ensure_unique_right(right, right_on)
        merged = left.merge(r_exact, how="left", left_on=left_on, right_on=right_on, suffixes=("", "_dim"))

        if audit:
            _prepare_audit_cols(merged)
            # Rows newly hit by exact = those that were miss before stage (all True) but have right key now (or any src)
            miss_before = pd.Series(True, index=merged.index)
            miss_after  = _miss_mask(merged, merged.index)
            filled = miss_before & ~miss_after
            # match_to as right_on (if present)
            mt = merged[right_on] if right_on in merged.columns else pd.Series(pd.NA, index=merged.index)
            merged.loc[filled, f"{left_on}_match_method"] = "exact"
            merged.loc[filled, f"{left_on}_match_score"]  = 100
            merged.loc[filled, f"{left_on}_match_to"]     = mt[filled]

    # ---------------- stage 2: normalized (fill only misses) ----------------
    if "normalized" in strategies:
        need = _miss_mask(merged, left.index)
        if isinstance(need, pd.Series) and need.any():
            base = left if merged is None else merged.loc[need].copy()
            base["_key_norm"] = _normalize_series(base[left_on], norm_steps)

            r_norm = right.copy()
            r_norm["_key_norm"] = _normalize_series(r_norm[right_on], norm_steps)
            r_norm = _ensure_unique_right(r_norm, "_key_norm")

            # Merge normalized key; use suffixes so right columns don't overwrite left columns
            fix = base.merge(
                r_norm, how="left", left_on="_key_norm", right_on="_key_norm", suffixes=("", "_dim")
            ).drop(columns=["_key_norm"], errors="ignore")

            if merged is None:
                merged = fix
            else:
                # Fill source columns only for 'need' rows
                for src in add_map.values():
                    mcol = _resolve_src_col(merged, src)
                    fcol = _resolve_src_col(fix, src)
                    if mcol and fcol:
                        merged.loc[need, mcol] = merged.loc[need, mcol].where(merged.loc[need, mcol].notna(), fix.loc[:, fcol])
                # Also fill right_on key if present in both (use resolved on fix)
                if right_on in merged.columns:
                    fkey = _resolve_src_col(fix, right_on) or right_on
                    if fkey in fix.columns:
                        merged.loc[need, right_on] = merged.loc[need, right_on].where(merged.loc[need, right_on].notna(), fix.loc[:, fkey])

            if audit:
                _prepare_audit_cols(merged)
                miss_after = _miss_mask(merged, merged.index)
                filled = need & ~miss_after
                merged.loc[filled, f"{left_on}_match_method"] = "normalized"
                merged.loc[filled, f"{left_on}_match_score"]  = 100
                # match_to: use right_on if present after fill
                if right_on in merged.columns:
                    merged.loc[filled, f"{left_on}_match_to"] = merged.loc[filled, right_on]

    # ---------------- stage 3: fuzzy (fill only remaining misses) ----------------
    if "fuzzy" in strategies:
        need = _miss_mask(merged, left.index)
        if isinstance(need, pd.Series) and need.any():
            base = merged.loc[need] if merged is not None else left.loc[need]
            left_vals  = base[left_on].astype(object)
            right_vals = right[right_on].astype(object)

            fcfg: FuzzyCfg = m.get("fuzzy", {})  # type: ignore[assignment]
            f_to, f_score = _fuzzy_match_series(
                left_vals, right_vals,
                normalize_steps=norm_steps,
                scorer_name=fcfg.get("scorer", "token_sort_ratio"),
                threshold=int(fcfg.get("threshold", 90)),
                top_k=int(fcfg.get("top_k", 1)),
            )

            tmp = base.copy()
            tmp["_match_key_tmp"] = f_to

            r_sub = _ensure_unique_right(right, right_on)
            fix = tmp.merge(r_sub, how="left", left_on="_match_key_tmp", right_on=right_on, suffixes=("", "_dim"))
            fix.drop(columns=["_match_key_tmp"], inplace=True, errors="ignore")

            if merged is None:
                merged = fix
            else:
                for src in add_map.values():
                    mcol = _resolve_src_col(merged, src)
                    fcol = _resolve_src_col(fix, src)
                    if mcol and fcol:
                        merged.loc[need, mcol] = merged.loc[need, mcol].where(merged.loc[need, mcol].notna(), fix.loc[:, fcol])
                if right_on in merged.columns and right_on in fix.columns:
                    merged.loc[need, right_on] = merged.loc[need, right_on].where(merged.loc[need, right_on].notna(), fix[right_on])

            if audit:
                _prepare_audit_cols(merged)
                # filled rows = need & (we actually found a match; f_to notna)
                filled = need & f_to.notna()
                merged.loc[filled, f"{left_on}_match_to"]     = f_to[filled]
                merged.loc[filled, f"{left_on}_match_score"]  = f_score[filled].astype("Int64")
                merged.loc[filled, f"{left_on}_match_method"] = "fuzzy"

    # ---------------- finalize ----------------
    if merged is None:
        merged = left.copy()

    # sort back to original order
    merged.sort_values("_ord__", inplace=True, kind="stable")
    merged.drop(columns=["_ord__"], inplace=True, errors="ignore")

    # drop duplicate right key if it leaked through (and differs from left key)
    # (Do this *after* audit has read right_on)
    if right_on in merged.columns and right_on != left_on:
        # Only drop if not expressly requested by add_map to be kept
        if right_on not in add_map.values():
            merged.drop(columns=[right_on], inplace=True, errors="ignore")

    # Collision-aware deferred rename: SOURCE → NEW
    if add_map:
        # Build a rename map that targets the resolved right-side columns
        rename_map: Dict[str, str] = {}
        collisions: List[str] = []
        for new, src in add_map.items():
            src_col = _resolve_src_col(merged, src)
            if not src_col:
                # source didn't arrive (no match) — skip rename now; the new col would remain absent or NaN
                continue
            if new in merged.columns and new != src_col:
                # Would overwrite an existing, different column
                collisions.append(new)
            else:
                rename_map[src_col] = new
        if collisions:
            raise ValueError(f"[enrich] add_map would overwrite existing columns: {collisions}")
        if rename_map:
            merged.rename(columns=rename_map, inplace=True)

    # Audit summary flag: did any NEW columns get filled?
    if audit and add_map:
        new_cols = [c for c in add_map.keys() if c in merged.columns]
        if new_cols:
            merged[f"{left_on}__enrich_hit"] = merged[new_cols].notna().any(axis=1)

    # on_miss policy (evaluate against NEW column names after rename)
    if on_miss == "fail" and add_map:
        new_cols = [c for c in add_map.keys() if c in merged.columns]
        if new_cols:
            miss = merged[new_cols].isna().all(axis=1) & merged[left_on].notna()
            if miss.any():
                # Provide a small sample with normalized value for easier debugging
                sample_idx = merged.index[miss][:10]
                sample = pd.DataFrame({
                    left_on: merged.loc[sample_idx, left_on].astype(object).tolist()
                }).to_dict(orient="records")
                raise ValueError(f"[enrich] no matches for some rows on '{left_on}'. Examples: {sample}")

    # Defer 'inner' filtering to after all stages (based on hit status)
    if how == "inner":
        if add_map:
            hit_cols = [c for c in add_map.keys() if c in merged.columns]
            if hit_cols:
                merged = merged[~merged[hit_cols].isna().all(axis=1)]
        else:
            # Fallback: if auditing was enabled, use match_method presence; otherwise, keep rows with right_on present (if any)
            col_method = f"{left_on}_match_method"
            if col_method in merged.columns:
                merged = merged[merged[col_method].notna()]
            elif right_on in merged.columns:
                merged = merged[merged[right_on].notna()]

    return merged
