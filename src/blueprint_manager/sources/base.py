from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd

from ..transforms import apply_pipeline
from ..utils.type_enforce import enforce_types, validate_frame
from ...modules.script_logger import logger
log = logger.get_logger()


class SourceAdapter(ABC):
    def __init__(self, source_cfg: Dict[str, Any], aliases: Dict[str, Any]):
        self.cfg = source_cfg
        self.aliases = aliases
    
    @abstractmethod
    def load_tables(self) -> dict[str, pd.DataFrame]:
        ...
    
    def _apply_column_mapping(self, df, columns_map):
        # map and apply transforms
        out = {}
        for src_col, spec in columns_map.items():
            alias = spec.get("alias") if isinstance(spec, dict) else None
            transforms = spec.get("transforms", []) if isinstance(spec, dict) else []
            col = df[src_col] if src_col in df.columns else pd.Series([None]*len(df))
            if transforms:
                col = apply_pipeline(col, transforms)
            out[alias or src_col] = col
        return pd.DataFrame(out)
    
    def _load_table_common(self, df: pd.DataFrame, table_cfg: Dict[str, Any]) -> pd.DataFrame:
        cols = table_cfg.get("columns", {})
        if cols:
            df = self._apply_column_mapping(df, cols)
        # Enforce and validate against schema aliases
        df = enforce_types(df, self.aliases)
        validate_frame(df, self.aliases)
        return df