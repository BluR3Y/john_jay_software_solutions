from __future__ import annotations
import pandas as pd

def run_validations(df, field_specs: dict[str, dict]) -> list[dict]:
    findings: list[dict] = []
    for col, spec in (field_specs or {}).items():
        # not_null
        if spec.get("not_null"):
            if col not in df.columns:
                findings.append({"column": col, "rule": "not_null", "count": "missing"})
            else:
                cnt = int(df[col].isna().sum())
                if cnt:
                    findings.append({"column": col, "rule": "not_null", "count": cnt})
        # allowed_values
        if "allowed_values" in spec and col in df.columns:
            bad_mask = ~df[col].isin(spec["allowed_values"])
            cnt = int(bad_mask.sum())
            if cnt:
                findings.append({"column": col, "rule": "allowed_values", "count": cnt})
        # identifier uniqueness
        if spec.get("identifier") and col in df.columns:
            dups = int(df[col].duplicated().sum())
            if dups:
                findings.append({"column": col, "rule": "unique_identifier", "count": dups})
    return findings