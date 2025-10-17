from __future__ import annotations
from typing import Dict, Any
import pandas as pd

from .base import SourceAdapter
from ...modules.script_logger import logger
log = logger.get_logger()

try:
    import pyodbc   # type: ignore
except Exception:   # pragma: no cover
    pyodbc = None

class AccessAdapter(SourceAdapter):
    def load_tables(self) -> dict[str, pd.DataFrame]:
        if pyodbc is None:
            raise RuntimeError("pyodbc not available. Install on Windows with Access DB Engine.")
        path = self.cfg.get("path")
        conn_str = f"Driver={{Microsoft Access Driver (*.mdb, *.accdb)}};DBQ={path};"
        cn = pyodbc.connect(conn_str)
        tables = {}
        for t in self.cfg.get("tables", []):
            name = t.get("name")
            table_id = t.get("table_id") or name
            log.info(f"Loading Access table '{name}' from {path}")
            df = pd.read_sql(f"SELECT * FROM [{name}]", cn)
            df = self._load_table_common(df, t)
            tables[table_id] = df
        cn.close()
        return tables