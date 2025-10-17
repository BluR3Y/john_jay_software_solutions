from __future__ import annotations
from typing import Dict, Any
import pandas as pd


from .base import SourceAdapter
from ...modules.script_logger import logger
log = logger.get_logger()

class ExcelAdapter(SourceAdapter):
    def load_tables(self) -> dict[str, pd.DataFrame]:
        path = self.cfg.get("path")
        tables = {}
        for t in self.cfg.get("tables", []):
            name = t.get("name")
            table_id = t.get("table_id") or name
            log.info(f"Loading Excel sheet '{name}' from {path}")
            df = pd.read_excel(path, sheet_name=name)
            df = self._load_table_common(df, t)
            tables[table_id] = df
        return tables