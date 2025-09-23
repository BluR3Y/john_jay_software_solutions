from __future__ import annotations
import pandas as pd
from .base import BaseAdapter

class ExcelAdapter(BaseAdapter):
    def load_table(self, table_name: str) -> pd.DataFrame:
        # Use dtype=str to keep raw strings; typing happens later
        return pd.read_excel(self.cfg["path"], sheet_name=table_name, dtype=str)