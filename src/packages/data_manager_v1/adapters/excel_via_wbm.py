from __future__ import annotations
import pandas as pd
from typing import Any, Optional
from .base import BaseAdapter

class ExcelViaWorkbookManager(BaseAdapter):
    def __init__(self, cfg: dict[str, Any], workbook_manager: Any) -> None:
        super().__init__(cfg)
        self.wbm = workbook_manager

    def load_table(self, table_name: str) -> pd.DataFrame:
        usecols: Optional[list[str]] = self.cfg.get("usecols")
        return self.wbm.read_sheet(path=self.cfg["path"], sheet=table_name, usecols=usecols)