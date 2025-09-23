from __future__ import annotations
from typing import Any, Dict
from pathlib import Path
import pandas as pd


from .transforms import apply_pipeline
from .filters import build_mask
from .utils.output_resolve import resolve_output_dir
from modules.script_logger import logger
log = logger.get_logger()




class Exporter:
    def __init__(self, output_dir: str | None):
        self.out_dir = resolve_output_dir(output_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)


    def export_workbook(self, wb_cfg: Dict[str, Any], compiled: dict[str, pd.DataFrame]):
        save_name = wb_cfg.get("save_name", "export") + ".xlsx"
        out_path = self.out_dir / save_name
        log.info(f"Exporting workbook: {out_path}")
        with pd.ExcelWriter(out_path, engine="openpyxl") as xl:
            for sheet in wb_cfg.get("sheets", []):
                name = sheet.get("name", "Sheet1")
                filt = sheet.get("filter") or {}
                columns = sheet.get("columns", {})
                # Choose a source to export from: by default the first compiled target
                # (Advanced: extend config with explicit `from_target` per sheet.)
                source_name = sheet.get("from", next(iter(compiled.keys())))
                df = compiled[source_name].copy()
                if filt:
                    df = df[build_mask(df, filt)].copy()
                # Map/transform columns
                out_map = {}
                for header, spec in columns.items():
                    alias = spec.get("alias") if isinstance(spec, dict) else str(spec)
                    series = df.get(alias)
                    if series is None:
                        out_map[header] = None
                        continue
                    steps = spec.get("transforms", []) if isinstance(spec, dict) else []
                    if steps:
                        series = apply_pipeline(series, steps)
                    out_map[header] = series
                out_df = pd.DataFrame(out_map)
                out_df.to_excel(xl, sheet_name=name, index=False)
        return str(out_path)