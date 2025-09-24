from __future__ import annotations
from typing import Dict, Any
import pandas as pd

from .base import SourceAdapter

class InlineAdapter(SourceAdapter):
    def load_tables(self) -> dict[str, pd.DataFrame]:
        tables: dict[str, pd.DataFrame] = {}
        for spec in self.cfg.get("data", []):
            table_id = spec["table_id"]   # now required
            orient = (spec.get("orient") or "records").lower()

            if orient == "records":
                df = pd.DataFrame(spec.get("rows") or [])
            elif orient == "columns":
                df = pd.DataFrame(spec.get("columns_payload") or {})
            else:
                raise ValueError(f"Unsupported inline orient: {orient}")

            df = self._load_table_common(df, spec)
            tables[table_id] = df
        return tables