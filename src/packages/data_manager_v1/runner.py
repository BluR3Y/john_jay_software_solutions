from __future__ import annotations
import json, os
from datetime import datetime
import pandas as pd

from .io.loader import AdapterRegistry, load_sources
from .normalize.aliaser import apply_aliases
from .normalize.typer import coerce_types
from .transform.registry import apply_column_plan, apply_row_plan
from .validate.rules import run_validations
from .compile.merge import compile_keyed
from .compile.snapshot import write_snapshot
from .compare.diff import keyed_diff
from .io.writer import write_diff_report

def run_with_config(cfg: dict, *, registry_kwargs: dict | None = None, write_snapshots: bool = True, write_reports: bool = True):
    registry_kwargs = registry_kwargs or {}
    registry = AdapterRegistry(**registry_kwargs)

    # 1) Load source tables
    tables = load_sources(cfg, registry)  # {table_id: df}

    # 2) Normalize each table: alias -> column transforms -> type -> row ops -> validate
    aliases_spec = cfg.get("schema", {}).get("aliases", cfg.get("aliases", {}))
    findings_by_table = {}
    for s in cfg.get("sources", cfg.get("files", [])):
        for t in s.get("tables", []):
            tid = t["table_id"]
            df = tables[tid]
            df = apply_aliases(df, t.get("columns", {}))
            df = apply_column_plan(df, t.get("transforms", {}).get("columns"))
            df = coerce_types(df, aliases_spec)
            df = apply_row_plan(df, t.get("transforms", {}).get("row"))
            tables[tid] = df
            findings_by_table[tid] = run_validations(df, aliases_spec)

    # 3) Compile targets
    compiled = {}
    compile_cfg = cfg.get("compile", {})
    now_ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    snap_cfg = cfg.get("output", {}).get("snapshots", {})
    snap_root = snap_cfg.get("path", "./snapshots")
    snap_fmt = snap_cfg.get("format", "parquet")

    for tgt in compile_cfg.get("targets", []):
        inputs = [tables[tid] for tid in tgt.get("inputs", []) if tid in tables]
        dfc = compile_keyed(inputs, tgt.get("key", []), tgt.get("merge_rules", {}), input_names=tgt.get("inputs"))
        # post transforms (columns only for simplicity; can add row ops similarly)
        dfc = apply_column_plan(dfc, tgt.get("post_transforms", {}).get("columns"))
        compiled[tgt["name"]] = dfc

        if write_snapshots:
            write_snapshot(dfc, snap_root, tgt["name"], now_ts, fmt=snap_fmt)

    # 4) Compare pairs
    # compare_cfg = cfg.get("compare", {})
    # reports_root = cfg.get("output", {}).get("reports", "./reports")
    compare_cfg = cfg.get("compare", {})
    # Normalize reports root: allow either a string or an object with {"path": "..."}
    _reports_cfg = cfg.get("output", {}).get("reports", "./reports")
    if isinstance(_reports_cfg, str):
        reports_root = _reports_cfg
    else:
        reports_root = _reports_cfg.get("path", "./reports")

    diffs = {}
    for pair in compare_cfg.get("pairs", []):
        # naive: both sides must be in `compiled`; in real use, you'd load previous snapshots
        left_name = pair["left"].split("@")[0]
        right_name = pair["right"].split("@")[0]
        left = compiled.get(left_name)
        right = compiled.get(right_name)
        if left is None or right is None:
            continue
        diff = keyed_diff(left, right, pair.get("on", []))
        diffs[f"{left_name}__vs__{right_name}"] = diff
        # if write_reports:
        #     write_diff_report(diff, reports_root, f"diff_{left_name}_vs_{right_name}", fmt=pair.get("output", {}).get("format", "excel"))
        if write_reports:
            # Honor per-pair output.path when provided, else use reports_root  auto base name.
            pair_out = pair.get("output", {}) or {}
            custom_path = pair_out.get("path")
            fmt = pair_out.get("format", "excel")
            if custom_path:
                from pathlib import Path
                p = Path(custom_path)
                out_dir = str(p.parent) if str(p.parent) not in ("", ".") else reports_root
                base_name = p.stem
                # Optional: infer fmt from extension if not explicitly set
                if "format" not in pair_out and p.suffix.lower() in {".xlsx", ".xls"}:
                    fmt = "excel"
                elif "format" not in pair_out and p.suffix.lower() == ".csv":
                    fmt = "csv"
            else:
                out_dir = reports_root
                base_name = f"diff_{left_name}_vs_{right_name}"
            write_diff_report(diff, out_dir, base_name, fmt=fmt)

    return {
        "tables": tables,
        "compiled": compiled,
        "findings": findings_by_table,
        "diffs": diffs,
        "timestamp": now_ts,
    }
