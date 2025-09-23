from __future__ import annotations
from typing import Any, Dict
from pathlib import Path
import pandas as pd


from .transforms import apply_pipeline
from .filters import build_mask
from .expr import eval_expr, ExprError
from .utils.output_resolve import resolve_output_dir
from modules.script_logger import logger
log = logger.get_logger()




class Exporter:
    def __init__(self, output_dir: str | None):
        self.out_dir = resolve_output_dir(output_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)


    def export_workbook(self, wb_cfg: Dict[str, Any], compiled: dict[str, pd.DataFrame]) -> str:
        save_name = wb_cfg.get("save_name", "export") + ".xlsx"
        out_path = self.out_dir / save_name
        log.info(f"Exporting workbook: {out_path}")

        created_any = False

        with pd.ExcelWriter(out_path, engine="openpyxl") as xl:
            for sheet in wb_cfg.get("sheets", []):
                name = sheet.get("name", "Sheet1")
                filt = sheet.get("filter") or {}
                columns = sheet.get("columns", {}) or {}
                source_name = sheet.get("from", next(iter(compiled.keys())))

                try:
                    df = compiled[source_name].copy()

                    if filt:
                        df = df[build_mask(df, filt)].copy()

                    # Build output columns
                    out_map: Dict[str, pd.Series] = {}
                    for header, spec in columns.items():
                        # normalize
                        spec = spec if isinstance(spec, dict) else {"alias": str(spec)}
                        series = None

                        # 1) pick the base data for this column
                        if "value" in spec:
                            # broadcast scalar to a Series
                            series = pd.Series([spec["value"]] * len(df), index=df.index)
                        elif "compute" in spec:
                            from .expr import eval_expr
                            series = eval_expr(df, spec["compute"])
                        elif "alias" in spec:
                            series = df.get(spec["alias"])
                        else:
                            series = None  # or raise if you want to enforce one of the above

                        # 2) apply transforms (NOW also for compute/value paths)
                        steps = spec.get("transforms", [])
                        if steps and series is not None:
                            series = apply_pipeline(series, steps)

                        out_map[header] = series

                    out_df = pd.DataFrame(out_map, index=df.index)

                    # optionally skip empty sheets
                    if out_df.empty:
                        log.warning(f"Sheet '{name}' produced 0 rows; skipping.")
                        continue

                    out_df.to_excel(xl, sheet_name=name, index=False)
                    created_any = True

                except Exception as e:
                    # Log and continue to try other sheets
                    log.exception(f"Sheet '{name}' failed: {e}. Skipping.")
                    continue

        # Ensure at least one visible sheet exists on disk
        if not created_any:
            with pd.ExcelWriter(out_path, engine="openpyxl") as xl:
                pd.DataFrame({"info": ["no data"]}).to_excel(xl, sheet_name="README", index=False)
            log.warning("No sheets written; emitted placeholder README sheet.")

        return str(out_path)