# utils/type_enforce.py (example)
import pandas as pd
from pandas.api import types as ptypes

def enforce_types(df: pd.DataFrame, aliases: dict[str, dict]) -> pd.DataFrame:
    out = df.copy()
    for name, spec in aliases.items():
        if name not in out.columns:
            continue
        typ = spec.get("type")
        if typ == "integer":
            out[name] = pd.to_numeric(out[name], errors="coerce").astype("Int64")
        elif typ == "number":
            out[name] = pd.to_numeric(out[name], errors="coerce")
        elif typ == "boolean":
            out[name] = out[name].astype("boolean")
        elif typ == "string":
            out[name] = out[name].astype("string")
        elif typ == "date":
            fmt = (spec.get("date") or {}).get("format")  # e.g., "%Y-%m-%d"
            out[name] = pd.to_datetime(out[name], format=fmt, errors="coerce")
        # identifiers / not_null checks can be validated later
    return out

def validate_frame(df: pd.DataFrame, aliases: dict[str, dict]) -> None:
    problems = []
    for name, spec in aliases.items():
        if name not in df.columns:
            continue
        if spec.get("not_null") and df[name].isna().any():
            problems.append(f"{name}: contains nulls but not_null=true")
        if "enum" in spec:
            bad = ~df[name].isin(spec["enum"]) & df[name].notna()
            if bad.any():
                uniq = list(df.loc[bad, name].astype(str).unique()[:5])
                problems.append(f"{name}: values outside enum (sample): {uniq}")
        if spec.get("identifier"):
            if df[name].isna().any() or df[name].duplicated().any():
                problems.append(f"{name}: identifier must be unique & non-null")
    if problems:
        raise ValueError("Schema validation failed:\n- " + "\n- ".join(problems))