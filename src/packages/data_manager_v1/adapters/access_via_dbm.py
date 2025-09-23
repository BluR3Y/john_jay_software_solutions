from __future__ import annotations
import pandas as pd
from typing import Any, Optional
from .base import BaseAdapter

class AccessViaDbManager(BaseAdapter):
    def __init__(self, cfg: dict[str, Any], db_manager: Any) -> None:
        super().__init__(cfg)
        self.dbm = db_manager

    def load_table(self, table_name: str) -> pd.DataFrame:
        cols: Optional[list[str]] = self.cfg.get("columns_select")
        where: Optional[str] = self.cfg.get("where")
        return self.dbm.read_table(db_path=self.cfg["path"], table=table_name, columns=cols, where=where)