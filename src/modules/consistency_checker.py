#!/usr/bin/env python3
"""
Alias-centric Excel Consistency Checker (pandas)

- Reads an alias-driven schema JSON
- Loads specified workbooks/sheets with minimal columns
- Applies alias-level and column-level mutations
- Canonicalizes to alias column names
- Auto-generates rules (unique on identifiers, equal_columns across tables for shared aliases)
- Applies allowed_values/not_null from aliases
- Evaluates rules and writes an Excel report (Issues + Summary)

Usage:
  python excel_alias_checker.py --schema schema.json --out report.xlsx [--preview-rules]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


# ===============================
# Utilities
# ===============================

def norm_colname(s: Any) -> str:
    s = "" if s is None else str(s)
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s

def canon_string(s: Any, *, case_insensitive: bool, ignore_ws: bool) -> Any:
    if pd.isna(s):
        return s
    t = str(s)
    if ignore_ws:
        t = t.strip()
        t = re.sub(r"\s+", " ", t)
    if case_insensitive:
        t = t.casefold()
    return t

def parse_dates_series(s: pd.Series, opts: Dict[str, Any]) -> pd.Series:
    """Coerce a Series to datetime with Excel serial or string parsing, then tz/granularity."""
    if s.empty:
        return pd.to_datetime(s, errors="coerce")

    excel_serial = bool(opts.get("excel_serial", False))
    fmt        = opts.get("format")
    dayfirst   = bool(opts.get("dayfirst", False))
    yearfirst  = bool(opts.get("yearfirst", False))
    origin     = opts.get("origin", "1899-12-30")  # Excel 1900 default
    tz         = opts.get("timezone")
    gran       = opts.get("granularity")
    # 1) base parsing
    if excel_serial:
        # force numeric → datetime (days from origin)
        num = pd.to_numeric(s, errors="coerce")
        dt  = pd.to_datetime(num, unit="d", origin=origin, errors="coerce")
    else:
        # format-aware, or generic fallback
        if fmt:
            dt = pd.to_datetime(s, format=fmt, errors="coerce")
        else:
            dt = pd.to_datetime(s, errors="coerce", dayfirst=dayfirst, yearfirst=yearfirst)
    # 2) timezone
    if tz:
        def _to_tz(x):
            if pd.isna(x):
                return x
            t = pd.Timestamp(x)
            if t.tzinfo is None:
                return t.tz_localize(tz)
            return t.tz_convert(tz)
        dt = dt.map(_to_tz)
    # 3) granularity
    if gran:
        if gran == "day":
            dt = dt.dt.normalize()
        else:
            dt = dt.dt.floor(gran)  # e.g., "H", "min", "s"
    return dt


# ===============================
# Mutations
# ===============================

def apply_mutations(series: pd.Series, mutations: List[Dict[str, Any]]) -> pd.Series:
    """Apply an ordered list of simple string/regex mutations to a Series."""
    if not mutations:
        return series
    s = series.astype("object")  # keep NaNs
    for m in mutations:
        op = m.get("op")
        if op == "trim":
            s = s.map(lambda x: x.strip() if isinstance(x, str) else x)
        elif op == "collapse_ws":
            s = s.map(lambda x: re.sub(r"\s+", " ", x) if isinstance(x, str) else x)
        elif op == "lower":
            s = s.map(lambda x: x.lower() if isinstance(x, str) else x)
        elif op == "upper":
            s = s.map(lambda x: x.upper() if isinstance(x, str) else x)
        elif op == "casefold":
            s = s.map(lambda x: x.casefold() if isinstance(x, str) else x)
        elif op == "strip_prefix":
            val = m.get("value", "")
            s = s.map(lambda x: x[len(val):] if isinstance(x, str) and x.startswith(val) else x)
        elif op == "strip_suffix":
            val = m.get("value", "")
            s = s.map(lambda x: x[:-len(val)] if isinstance(x, str) and x.endswith(val) and len(val) > 0 else x)
        elif op == "regex_replace":
            pat = m.get("pattern", "")
            rep = m.get("repl", "")
            flags = m.get("flags", "")
            re_flags = 0
            if "i" in flags: re_flags |= re.IGNORECASE
            if "m" in flags: re_flags |= re.MULTILINE
            rx = re.compile(pat, re_flags)
            s = s.map(lambda x: rx.sub(rep, x) if isinstance(x, str) else x)
        elif op == "fillna":
            val = m.get("value", None)
            s = s.fillna(val)
        elif op == "to_number":
            s = pd.to_numeric(s, errors="coerce")
        else:
            # unknown op -> ignore silently
            pass
    return s


# ===============================
# Schema dataclasses
# ===============================

@dataclass
class AliasSpec:
    name: str
    type: str = "string"  # string | number | date (date unused in comparisons here)
    identifier: bool = False
    not_null: bool = False
    allowed_values: Optional[List[Any]] = None
    mutations: List[Dict[str, Any]] = field(default_factory=list)
    numeric: Dict[str, Any] = field(default_factory=dict)  # {decimals, abs_tol, rel_tol}
    compare: Dict[str, Any] = field(default_factory=dict)  # {case_insensitive, ignore_whitespace}
    date: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ColumnMap:
    source: str
    alias: str
    mutations: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class SheetSpec:
    name: str
    table_id: str
    columns: List[ColumnMap]

@dataclass
class FileSpec:
    id: str
    path: str
    sheets: List[SheetSpec]

@dataclass
class Schema:
    files: List[FileSpec]
    aliases: Dict[str, AliasSpec]
    compare_defaults: Dict[str, Any] = field(default_factory=lambda: {"case_insensitive": True, "ignore_whitespace": True})
    rules_extra: List[Dict[str, Any]] = field(default_factory=list)

    @staticmethod
    def from_json(d: Dict[str, Any]) -> "Schema":
        aliases = {}
        for name, a in d.get("aliases", {}).items():
            aliases[name] = AliasSpec(
                name=name,
                type=a.get("type", "string"),
                identifier=bool(a.get("identifier", False)),
                not_null=bool(a.get("not_null", False)),
                allowed_values=a.get("allowed_values"),
                mutations=a.get("mutations", []) or [],
                numeric=a.get("numeric", {}) or {},
                compare=a.get("compare", {}) or {},
                date=a.get("date", {}) or {},
            )
        files = []
        for f in d.get("files", []):
            sheets = []
            for s in f.get("sheets", []):
                cols = []
                if isinstance(s.get("columns"), dict):
                    for src, meta in s["columns"].items():
                        if isinstance(meta, dict):
                            cols.append(ColumnMap(source=src, alias=meta["alias"], mutations=meta.get("mutations", []) or []))
                        else:
                            # meta is alias name string
                            cols.append(ColumnMap(source=src, alias=str(meta), mutations=[]))
                elif isinstance(s.get("columns"), list):
                    for entry in s["columns"]:
                        cols.append(ColumnMap(source=entry["source"], alias=entry["alias"], mutations=entry.get("mutations", []) or []))
                else:
                    cols = []
                sheets.append(SheetSpec(name=s["name"], table_id=s["table_id"], columns=cols))
            files.append(FileSpec(id=f["id"], path=f["path"], sheets=sheets))
        return Schema(
            files=files,
            aliases=aliases,
            compare_defaults=d.get("compare", {"case_insensitive": True, "ignore_whitespace": True}),
            rules_extra=d.get("rules_extra", []) or [],
        )


# ===============================
# Loading tables
# ===============================

@dataclass
class Table:
    id: str
    df: pd.DataFrame
    source_path: str
    sheet_name: str
    present_aliases: List[str]

def load_tables(schema: Schema) -> Tuple[Dict[str, Table], List[str]]:
    """Load all configured sheets with minimal columns, apply mappings and mutations. Return tables and global identifier aliases list."""
    # global set of identifier aliases
    id_aliases = [a.name for a in schema.aliases.values() if a.identifier]
    id_aliases = sorted(id_aliases)

    tables: Dict[str, Table] = {}

    for f in schema.files:
        file_path = Path(f.path)
        for s in f.sheets:
            # columns to read
            usecols = [c.source for c in s.columns]
            # read the sheet
            try:
                raw = pd.read_excel(file_path, sheet_name=s.name, usecols=usecols, engine=None)
            except Exception as e:
                raise RuntimeError(f"Failed reading {file_path} sheet '{s.name}': {e}")
            df = raw.copy()
            # rename source -> alias
            rename_map = {c.source: c.alias for c in s.columns}
            df.rename(columns=rename_map, inplace=True)
            # normalize headers
            df.columns = [norm_colname(x) for x in df.columns]

            # apply per-column mutations from mapping
            for c in s.columns:
                if c.alias in df.columns and c.mutations:
                    df[c.alias] = apply_mutations(df[c.alias], c.mutations)

            # apply alias-level mutations and type coercions
            present_aliases = []
            for alias_name, alias in schema.aliases.items():
                if alias_name in df.columns:
                    present_aliases.append(alias_name)
                    if alias.mutations:
                        df[alias_name] = apply_mutations(df[alias_name], alias.mutations)
                    # type coercion
                    if alias.type == "date":
                        df[alias_name] = parse_dates_series(df[alias_name], alias.date)
                    elif alias.type == "number":
                        df[alias_name] = pd.to_numeric(df[alias_name], errors="coerce")
                    elif alias.type == "string":
                        pass
                    # if alias.type == "number":
                    #     df[alias_name] = pd.to_numeric(df[alias_name], errors="coerce")
                    # elif alias.type == "string":
                    #     # keep as object, but ensure consistent string ops later
                    #     pass
                    # # TODO: date parsing if needed
            tables[s.table_id] = Table(
                id=s.table_id,
                df=df,
                source_path=str(file_path),
                sheet_name=s.name,
                present_aliases=present_aliases,
            )
    return tables, id_aliases


# ===============================
# Rule generation
# ===============================

@dataclass
class Rule:
    id: str
    type: str  # equal_columns | unique | not_null | allowed_values | expression
    # equal_columns
    left_table: Optional[str] = None
    right_table: Optional[str] = None
    alias: Optional[str] = None
    # single-table
    table: Optional[str] = None
    column: Optional[str] = None
    # compare options
    case_insensitive: Optional[bool] = None
    ignore_whitespace: Optional[bool] = None
    decimals: Optional[int] = None
    abs_tol: Optional[float] = None
    rel_tol: Optional[float] = None
    # extra
    severity: str = "error"
    expression: Optional[str] = None

def generate_rules(schema: Schema, tables: Dict[str, Table], id_aliases: List[str]) -> List[Rule]:
    rules: List[Rule] = []

    # Collect which tables have all identifier aliases
    tables_with_ids = [tid for tid, t in tables.items() if all(a in t.df.columns for a in id_aliases)] if id_aliases else list(tables.keys())

    # UNIQUE on identifiers per table
    if id_aliases:
        for tid in tables_with_ids:
            rid = f"unique_ids:{tid}"
            rules.append(Rule(id=rid, type="unique", table=tid, column="||".join(id_aliases), severity="error"))

    # NOT_NULL and ALLOWED_VALUES from alias specs, per table
    for alias_name, alias in schema.aliases.items():
        for tid, t in tables.items():
            if alias_name in t.df.columns:
                if alias.not_null:
                    rules.append(Rule(id=f"not_null:{tid}:{alias_name}", type="not_null", table=tid, column=alias_name, severity="error"))
                if alias.allowed_values:
                    rules.append(Rule(id=f"allowed_values:{tid}:{alias_name}", type="allowed_values", table=tid, column=alias_name, severity="error"))

    # EQUAL_COLUMNS across tables for shared aliases
    # Build alias -> list of tables that contain it (and have all id keys if needed)
    alias_tables: Dict[str, List[str]] = {}
    for tid, t in tables.items():
        for a in t.present_aliases:
            alias_tables.setdefault(a, []).append(tid)
    for alias_name, tids in alias_tables.items():
        if len(tids) < 2:
            continue
        # Compare across all pairs, but only if both have identifiers when identifiers exist
        for left, right in combinations(tids, 2):
            if id_aliases and (left not in tables_with_ids or right not in tables_with_ids):
                continue
            alias = schema.aliases.get(alias_name, AliasSpec(alias_name))
            # comparison settings resolve
            case_ins = alias.compare.get("case_insensitive", schema.compare_defaults.get("case_insensitive", True))
            ign_ws = alias.compare.get("ignore_whitespace", schema.compare_defaults.get("ignore_whitespace", True))
            dec = alias.numeric.get("decimals")
            abs_tol = alias.numeric.get("abs_tol")
            rel_tol = alias.numeric.get("rel_tol")
            rid = f"equal:{alias_name}:{left}=={right}"
            rules.append(Rule(
                id=rid, type="equal_columns",
                left_table=left, right_table=right, alias=alias_name,
                case_insensitive=case_ins, ignore_whitespace=ign_ws,
                decimals=dec, abs_tol=abs_tol, rel_tol=rel_tol,
                severity="error"
            ))

    # EXTRA rules (expression etc.)
    for r in schema.rules_extra:
        if r.get("type") == "expression":
            rules.append(Rule(
                id=r["id"], type="expression", table=r["table"], expression=r["expr"], severity=r.get("severity", "warn")
            ))

    return rules


# ===============================
# Rule evaluation
# ===============================

@dataclass
class Issue:
    rule_id: str
    severity: str
    table_left: Optional[str] = None
    table_right: Optional[str] = None
    alias: Optional[str] = None
    key_values: Optional[Dict[str, Any]] = None
    value_left: Any = None
    value_right: Any = None
    detail: str = ""

def build_composite_key(df: pd.DataFrame, keys: List[str]) -> pd.Series:
    if not keys:
        # fallback: row index as key
        return pd.Series(df.index.astype(str), index=df.index)
    parts = []
    for k in keys:
        if k not in df.columns:
            parts.append(pd.Series(["<missing>"] * len(df), index=df.index))
        else:
            # string-safe key part
            v = df[k].astype("object").map(lambda x: "" if pd.isna(x) else str(x))
            parts.append(v)
    key = parts[0]
    for p in parts[1:]:
        key = key + "||" + p
    return key

def compare_values(a: Any, b: Any, *, alias: AliasSpec, defaults: Dict[str, Any], decimals: Optional[int], abs_tol: Optional[float], rel_tol: Optional[float]) -> bool:
    # Both NaN -> equal if not_null not enforced
    if pd.isna(a) and pd.isna(b):
        return True

    # numeric
    if alias.type == "number":
        try:
            fa = float(a) if a is not None and a == a else float("nan")
            fb = float(b) if b is not None and b == b else float("nan")
        except Exception:
            return a == b
        if pd.isna(fa) and pd.isna(fb):
            return True
        if decimals is not None:
            fa = round(fa, decimals)
            fb = round(fb, decimals)
        if abs_tol is not None and abs(fa - fb) <= abs_tol:
            return True
        if rel_tol is not None:
            denom = max(abs(fa), abs(fb), 1e-12)
            if abs(fa - fb) / denom <= rel_tol:
                return True
        return fa == fb
    
    # Date
    if alias.type == "date":
        # Coerce both to Timestamp
        ta = pd.to_datetime(a, errors="coerce")
        tb = pd.to_datetime(b, errors="coerce")
        if pd.isna(ta) and pd.isna(tb):
            return True
        # Granularity normalization (mirror loader for safety)
        gran = alias.date.get("granularity")
        if gran:
            if gran == "day":
                if not pd.isna(ta): ta = pd.Timestamp(ta).normalize()
                if not pd.isna(tb): tb = pd.Timestamp(tb).normalize()
            else:
                if not pd.isna(ta): ta = pd.Timestamp(ta).floor(gran)
                if not pd.isna(tb): tb = pd.Timestamp(tb).floor(gran)
        # Absolute tolerance
        tol_str = alias.date.get("abs_tol")
        if tol_str:
            try:
                tol = pd.Timedelta(tol_str)
                if not (pd.isna(ta) or pd.isna(tb)):
                    return abs(ta - tb) <= tol
            except Exception:
                pass
        # Default exact equality (after granularity)
        return pd.isna(ta) and pd.isna(tb) or ta == tb

    # string
    case_insensitive = alias.compare.get("case_insensitive", defaults.get("case_insensitive", True))
    ignore_ws = alias.compare.get("ignore_whitespace", defaults.get("ignore_whitespace", True))
    if isinstance(a, str) or isinstance(b, str):
        sa = canon_string(a, case_insensitive=case_insensitive, ignore_ws=ignore_ws)
        sb = canon_string(b, case_insensitive=case_insensitive, ignore_ws=ignore_ws)
        return sa == sb

    # default
    return a == b

def evaluate_rules(schema: Schema, tables: Dict[str, Table], id_aliases: List[str], rules: List[Rule]) -> pd.DataFrame:
    issues: List[Issue] = []

    for r in rules:
        if r.type == "unique":
            t = tables[r.table]
            # unique on composite ids
            keys = id_aliases
            if not keys:
                continue
            key_series = build_composite_key(t.df, keys)
            dup_mask = key_series.duplicated(keep=False)
            dup_rows = t.df[dup_mask]
            for idx, _ in dup_rows.iterrows():
                issues.append(Issue(
                    rule_id=r.id, severity=r.severity, table_left=r.table, alias="|".join(keys),
                    key_values={"row_index": int(idx), "key": key_series.loc[idx]}, detail="Duplicate identifier",
                ))
        elif r.type == "not_null":
            t = tables[r.table]
            col = r.column
            if col not in t.df.columns:
                continue
            s = t.df[col]
            mask = s.isna() | (s.astype(str).str.strip() == "")
            bad = t.df[mask]
            for idx, _ in bad.iterrows():
                issues.append(Issue(
                    rule_id=r.id, severity=r.severity, table_left=r.table, alias=col, key_values={"row_index": int(idx)},
                    value_left=t.df.at[idx, col], detail="Null/blank value",
                ))
        elif r.type == "allowed_values":
            t = tables[r.table]
            col = r.column
            alias_spec = schema.aliases.get(col, AliasSpec(col))
            allowed = alias_spec.allowed_values or []
            if col not in t.df.columns:
                continue
            s = t.df[col]
            bad_mask = ~s.isin(allowed)
            bad = t.df[bad_mask]
            for idx, _ in bad.iterrows():
                issues.append(Issue(
                    rule_id=r.id, severity=r.severity, table_left=r.table, alias=col,
                    key_values={"row_index": int(idx)}, value_left=t.df.at[idx, col],
                    detail=f"Value not allowed; expected one of {allowed[:5]}{'...' if len(allowed)>5 else ''}"
                ))
        elif r.type == "equal_columns":
            lt = tables[r.left_table]; rt = tables[r.right_table]
            alias_name = r.alias
            alias_spec = schema.aliases.get(alias_name, AliasSpec(alias_name))
            # Build key series
            key_left = build_composite_key(lt.df, id_aliases)
            key_right = build_composite_key(rt.df, id_aliases)
            left_series = pd.Series(lt.df[alias_name].values, index=key_left, name="left") if alias_name in lt.df.columns else pd.Series(dtype="object")
            right_series = pd.Series(rt.df[alias_name].values, index=key_right, name="right") if alias_name in rt.df.columns else pd.Series(dtype="object")
            align = pd.concat([left_series, right_series], axis=1)  # outer join by index
            for key, row in align.iterrows():
                a = row.get("left", None)
                b = row.get("right", None)
                # both missing treated as ok
                if pd.isna(a) and pd.isna(b):
                    continue
                equal = compare_values(a, b, alias=alias_spec, defaults=schema.compare_defaults, decimals=r.decimals, abs_tol=r.abs_tol, rel_tol=r.rel_tol)
                if not equal:
                    issues.append(Issue(
                        rule_id=r.id, severity=r.severity, table_left=r.left_table, table_right=r.right_table, alias=alias_name,
                        key_values={"key": key}, value_left=a, value_right=b, detail="Values differ"
                    ))
        elif r.type == "expression":
            t = tables[r.table]
            expr = r.expression
            try:
                cond = t.df.eval(expr)
            except Exception as e:
                raise ValueError(f"Bad expression in rule {r.id}: {e}")
            bad = t.df[~cond.fillna(False)]
            for idx, _ in bad.iterrows():
                issues.append(Issue(
                    rule_id=r.id, severity=r.severity, table_left=r.table, alias=None, key_values={"row_index": int(idx)},
                    detail=f"Row does not satisfy expression: {expr}"
                ))
        else:
            raise ValueError(f"Unknown rule type {r.type}")

    # to DataFrame
    rows = []
    for it in issues:
        rows.append({
            "rule_id": it.rule_id,
            "severity": it.severity,
            "table_left": it.table_left,
            "table_right": it.table_right,
            "alias": it.alias,
            "key_values": json.dumps(it.key_values) if it.key_values is not None else None,
            "value_left": it.value_left,
            "value_right": it.value_right,
            "detail": it.detail,
        })
    return pd.DataFrame.from_records(rows)


# ===============================
# Reporting
# ===============================

def write_report(issues_df: pd.DataFrame, out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    summary = (
        issues_df.groupby(["severity", "rule_id"], dropna=False)
        .size()
        .reset_index(name="count")
        .sort_values(["severity", "count"], ascending=[True, False])
    )
    with pd.ExcelWriter(out_path, engine="openpyxl") as xl:
        issues_df.to_excel(xl, sheet_name="Issues", index=False)
        summary.to_excel(xl, sheet_name="Summary", index=False)


# ===============================
# CLI
# ===============================

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Alias-centric Excel Consistency Checker")
    ap.add_argument("--schema", required=True, help="Path to schema JSON")
    ap.add_argument("--out", required=True, help="Path to output Excel report")
    ap.add_argument("--preview-rules", action="store_true", help="Print derived rules and exit")
    args = ap.parse_args(argv)

    schema_path = Path(args.schema)
    if not schema_path.exists():
        print(f"Schema not found: {schema_path}", file=sys.stderr)
        return 2

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_json = json.load(f)
    schema = Schema.from_json(schema_json)

    tables, id_aliases = load_tables(schema)
    rules = generate_rules(schema, tables, id_aliases)

    if args.preview_rules:
        print(json.dumps([r.__dict__ for r in rules], indent=2, default=str))
        return 0

    issues = evaluate_rules(schema, tables, id_aliases, rules)
    write_report(issues, Path(args.out))
    print(f"Wrote report to {args.out} with {len(issues)} issues.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
