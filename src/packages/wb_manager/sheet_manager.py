from __future__ import annotations

from typing import (
    Any, Dict, Iterable,
    List, Mapping, Optional,
    Sequence, Tuple, Literal
)
import pandas as pd
import numpy as np

class SheetManager:
    """
    Manage a single sheet's DataFrame, perform lookups, and prepare annotations.
    """
    def __init__(self, name: str, df: pd.DataFrame) -> None:
        self.name = name
        self.df = df
        # Stores annotations as tuples
        self._annotations: List[Tuple[int, int, str, str]] = []
    
    # --------------------------- Data access / utility ---------------------------
    def get_df(self, *, format: bool = False) -> pd.DataFrame:
        """
        Return internal DataFrame. If `format` is True, normalize NaN/NaT to None and coerce
        pandas Timestamps to python datetimes for easier Excel writes.
        """
        if not format:
            return self.df
        clean = self.df.copy()
        for c in clean.columns:
            if pd.api.types.is_datetime64_any_dtype(clean[c]):
                clean[c] = clean[c].dt.to_pydatetime()
        clean = clean.where(pd.notnull(clean), None)
        return clean
    
    def update_cell(self, row: int, col: int | str, value: Any) -> None:
        """In-place update of a single cell (0-based row/col)."""
        if isinstance(col, str):
            try:
                col = list(self.df.columns).index(col)
            except ValueError:
                raise ValueError(f"{col!r} is not a valid column name in sheet '{self.name}'.")
        n_rows, n_cols = self.df.shape
        if not (0 <= row < n_rows) or not (0 <= col < n_cols):
            raise IndexError("Index is out of bounds.")
        self.df.iat[row, col] = value

    def append_row(self, values: Mapping[str, Any]) -> None:
        """Append a row given a mapping of column -> value. Missing cols are filled with NaN."""
        row = {c: np.nan for c in self.df.columns}
        row.update({k: v for k, v in values.items() if k in self.df.columns})
        self.df.loc[len(self.df)] = row
    
    def delete_row(self, row: int) -> None:
        self.df.drop(index=row, inplace=True)
        self.df.reset_index(drop=True, inplace=True)
    
    # --------------------------- Issues / annotations ---------------------------
    def add_annotation(self, row: int, col: int | str, level: Literal["info", "warn", "error"], message: str) -> None:
        """Record an annotation in Excel (performed by the I/O layer)."""
        if isinstance(col, str):
            try:
                col = list(self.df.columns).index(col)
            except ValueError:
                raise ValueError(f"{col!r} is not a valid column name in sheet '{self.name}'.")
        n_rows, n_cols = self.df.shape
        if not (0 <= row < n_rows) or not (0 <= col < n_cols):
            raise IndexError("Index is out of bounds.")
        self._annotations.append((row, col, level, message))
    
    def iter_annotations(self) -> Iterable[Tuple[int, int, str, str]]:
        return iter(self._annotations)
    
    def clear_annotations(self) -> None:
        self._annotations.clear()

    # --------------------------- Find logic ---------------------------
    def find(
        self,
        query: Mapping[str, Any],
        *,
        candidates: Optional[pd.DataFrame] = None
    ) -> pd.DataFrame:
        # exact match, no score column
        return self.match(query, candidates=candidates, threshold=1.0, include_score=False)

    def match(
        self,
        query: Mapping[str, Any],
        *,
        candidates: Optional[pd.DataFrame] = None,
        threshold: float = 0.6,
        include_score: bool = True,
        best_only: bool = False,
        nulls_match: bool = False,
    ) -> pd.DataFrame:
        # To remove __score__ from returned DF: res.pop("__score__")
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be in [0.0, 1.0]")
        if not query:
            return self.df.iloc[0:0].copy()

        df = candidates if candidates is not None else self.df
        if df.empty:
            return df.iloc[0:0].copy()

        keys = [k for k in query.keys() if k in df.columns]
        if not keys:
            return df.iloc[0:0].copy()

        if threshold >= 1.0:
            # exact path
            mask = pd.Series(True, index=df.index)
            for k in keys:
                mask &= (df[k] == query[k])
            out = df[mask].copy()
            if include_score:
                out["__score__"] = 1.0
            if best_only and not out.empty:
                return out.iloc[[0]]
            return out

        # fuzzy path
        qser = pd.Series({k: query[k] for k in keys})
        comp = df[keys].eq(qser)

        if nulls_match:
            # treat NaN==NaN as a match
            comp |= (df[keys].isna() & pd.isna(qser))

        scores = comp.sum(axis=1) / float(len(keys))
        keep = scores >= float(threshold)
        out = df.loc[keep].copy()
        if include_score:
            out["__score__"] = scores[keep].astype(float)
            out.sort_values("__score__", ascending=False, inplace=True)
        if best_only:
            return out.iloc[[0]] if not out.empty else out
        return out
