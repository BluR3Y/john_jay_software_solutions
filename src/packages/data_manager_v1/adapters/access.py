from __future__ import annotations
import pandas as pd
from .base import BaseAdapter

class AccessAdapter(BaseAdapter):
    def _conn(self):
        try:
            import pyodbc  # optional
        except Exception as e:
            raise RuntimeError("pyodbc not installed. Install with extras: consistencyx[access]") from e
        dsn = self.cfg.get("odbc_dsn")
        if dsn:
            return pyodbc.connect(f"DSN={dsn};")
        path = self.cfg["path"]
        return pyodbc.connect(f'DRIVER={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};')

    def load_table(self, table_name: str) -> pd.DataFrame:
        with self._conn() as conn:
            return pd.read_sql(f"SELECT * FROM [{table_name}]", conn)