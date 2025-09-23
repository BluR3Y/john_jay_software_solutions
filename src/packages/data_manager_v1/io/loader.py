from __future__ import annotations
from typing import Any, Callable, Dict, Mapping
from pathlib import Path
import pandas as pd

from ..adapters.base import BaseAdapter
from ..adapters.excel import ExcelAdapter as BuiltinExcel
from ..adapters.access import AccessAdapter as BuiltinAccess

try:
    from ..adapters.excel_via_wbm import ExcelViaWorkbookManager
except Exception:
    ExcelViaWorkbookManager = None  # type: ignore
try:
    from ..adapters.access_via_dbm import AccessViaDbManager
except Exception:
    AccessViaDbManager = None  # type: ignore

class SourceTypeUnknownError(ValueError): ...
class AdapterNotAvailableError(RuntimeError): ...

def infer_type_from_path(path: str) -> str | None:
    ext = Path(path).suffix.lower()
    if ext in {".xlsx", ".xlsm", ".xls"}: return "excel"
    if ext in {".accdb", ".mdb"}: return "access"
    if ext in {".csv"}: return "csv"
    return None

class AdapterRegistry:
    def __init__(self, *, workbook_manager: Any | None = None, db_manager: Any | None = None,
                 extra_factories: Mapping[str, Callable[[dict[str, Any]], BaseAdapter]] | None = None) -> None:
        self._factories: Dict[str, Callable[[dict[str, Any]], BaseAdapter]] = {
            "excel": lambda cfg: BuiltinExcel(cfg),
            "access": lambda cfg: BuiltinAccess(cfg),
        }
        if workbook_manager is not None and ExcelViaWorkbookManager is not None:
            self._factories["excel"] = lambda cfg: ExcelViaWorkbookManager(cfg, workbook_manager)
        if db_manager is not None and AccessViaDbManager is not None:
            self._factories["access"] = lambda cfg: AccessViaDbManager(cfg, db_manager)
        if extra_factories:
            self._factories.update(extra_factories)

    def make(self, source_cfg: dict[str, Any]) -> BaseAdapter:
        typ = source_cfg.get("type") or infer_type_from_path(source_cfg.get("path", ""))
        if not typ:
            raise SourceTypeUnknownError(f"Cannot infer adapter type for: {source_cfg!r}")
        factory = self._factories.get(typ)
        if not factory:
            raise AdapterNotAvailableError(f"No adapter factory for type '{typ}'")
        return factory(source_cfg)

def load_sources(cfg: dict[str, Any], registry: AdapterRegistry) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for s in cfg.get("sources", cfg.get("files", [])):
        adapter = registry.make(s)
        for t in s.get("tables", []):
            name, tid = t["name"], t["table_id"]
            df = adapter.load_table(name)
            out[tid] = df
    return out
