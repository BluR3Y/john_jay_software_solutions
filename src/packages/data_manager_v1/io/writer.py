from __future__ import annotations
from pathlib import Path
import pandas as pd
from typing import Dict

def write_diff_report(diff: dict, out_dir: str, base_name: str, fmt: str = "excel") -> str:
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    if fmt == "excel":
        path = Path(out_dir) / f"{base_name}.xlsx"
        try:
            with pd.ExcelWriter(path) as xw:
                diff.get("added", pd.DataFrame()).to_excel(xw, index=False, sheet_name="added")
                diff.get("removed", pd.DataFrame()).to_excel(xw, index=False, sheet_name="removed")
                changes = diff.get("changes", {})
                for col, df in changes.items():
                    df.to_excel(xw, index=False, sheet_name=f"chg_{col[:28]}")
        except Exception:
            # fallback to CSVs
            path = Path(out_dir) / f"{base_name}"
            (Path(out_dir) / f"{base_name}_added.csv").write_text(diff.get("added", pd.DataFrame()).to_csv(index=False))
            (Path(out_dir) / f"{base_name}_removed.csv").write_text(diff.get("removed", pd.DataFrame()).to_csv(index=False))
            for col, df in diff.get("changes", {}).items():
                (Path(out_dir) / f"{base_name}_chg_{col}.csv").write_text(df.to_csv(index=False))
            return str(path)
        return str(path)
    else:
        # write as CSV bundle
        prefix = Path(out_dir) / base_name
        diff.get("added", pd.DataFrame()).to_csv(f"{prefix}_added.csv", index=False)
        diff.get("removed", pd.DataFrame()).to_csv(f"{prefix}_removed.csv", index=False)
        for col, df in diff.get("changes", {}).items():
            df.to_csv(f"{prefix}_chg_{col}.csv", index=False)
        return str(prefix)
