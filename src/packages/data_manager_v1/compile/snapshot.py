from __future__ import annotations
from pathlib import Path
import pandas as pd

def write_snapshot(df: pd.DataFrame, root: str, name: str, ts: str, fmt: str = "parquet") -> str:
    Path(root).mkdir(parents=True, exist_ok=True)
    path = Path(root) / f"{name}_{ts}.{fmt}"
    if fmt == "parquet":
        try:
            df.to_parquet(path)
        except Exception:
            # fallback to CSV if parquet engine unavailable
            path = Path(root) / f"{name}_{ts}.csv"
            df.to_csv(path, index=False)
    elif fmt == "csv":
        df.to_csv(path, index=False)
    else:
        df.to_pickle(path)
    return str(path)