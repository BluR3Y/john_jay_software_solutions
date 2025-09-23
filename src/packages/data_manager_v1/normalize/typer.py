from __future__ import annotations
import pandas as pd

def coerce_types(df, field_specs: dict[str, dict]):
    for name, spec in (field_specs or {}).items():
        if name not in df.columns: 
            continue
        t = spec.get("type")
        if t == "number":
            df[name] = pd.to_numeric(df[name], errors="coerce")
        elif t == "integer":
            df[name] = pd.to_numeric(df[name], errors="coerce").astype("Int64")
        elif t == "date":
            date_cfg = spec.get("date", {})
            fmt = date_cfg.get("format")
            if fmt:
                df[name] = pd.to_datetime(df[name], format=fmt, errors="coerce")
            else:
                df[name] = pd.to_datetime(df[name], errors="coerce")
        elif t == "bool":
            df[name] = df[name].astype("string").str.strip().str.lower().map({
                "true": True, "t": True, "yes": True, "y": True, "1": True,
                "false": False, "f": False, "no": False, "n": False, "0": False
            })
        elif t == "string":
            df[name] = df[name].astype("string")
    return df
