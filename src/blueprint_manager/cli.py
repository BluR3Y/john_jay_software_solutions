from __future__ import annotations
import argparse
from pathlib import Path
import json
import pandas as pd


from .config_loader import load_config
from .models import Config
from modules.script_logger import logger
log = logger.get_logger()
from .sources.excel_adapter import ExcelAdapter
from .sources.access_adapter import AccessAdapter
from .sources.inline_adapter import InlineAdapter
from .compile_engine import Compiler
from .compare_engine import write_compare_workbook
# from .compare_engine import Comparator
from .export_engine import Exporter

def _select_adapter(src: dict, aliases: dict):
    if "data" in src:
        return InlineAdapter(src, aliases)
    path = (src.get("path") or "").lower()
    if path.endswith((".xlsx", ".xls", ".xlsb")):
        return ExcelAdapter(src, aliases)
    if path.endswith((".accdb", ".mdb")):
        return AccessAdapter(src, aliases)
    raise RuntimeError(f"Unrecognized source type: {src}")

def _load_sources(cfg: Config) -> dict[str, pd.DataFrame]:
    frames: dict[str, pd.DataFrame] = {}
    aliases = cfg.schema_aliases

    for src in cfg.sources:
        adapter = _select_adapter(src, aliases)
        frames.update(adapter.load_tables())
    return frames


def _compile_all(cfg: Config, frames: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    compiler = Compiler(frames)
    compiled = {}
    for tgt in cfg.compile_targets:
        compiled[tgt["name"]] = compiler.compile_target(tgt)
    return compiled


# def _compare_all(cfg: Config, compiled: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
#     comparator = Comparator(compiled)
#     reports = {}
#     for pair in cfg.compare_pairs:
#         name = pair.get("save_name") or f"{pair['left']}_vs_{pair['right']}"
#         reports[name] = comparator.compare_pair(pair)
#     return reports

def _compare_all(cfg, compiled):
    for pair in cfg.compare_pairs:
        write_compare_workbook(compiled[pair["left"]], compiled[pair["right"]], pair.get("key_cols"), pair.get("compare_cols"), pair.get("path"))

def _export_all(cfg: Config, compiled: dict[str, pd.DataFrame]) -> list[str]:
    exporter = Exporter(cfg.output)
    paths = []
    for wb in cfg.export_workbooks:
        paths.append(exporter.export_workbook(wb, compiled))
    return paths

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser("blueprint-manager")
    sub = ap.add_subparsers(dest="cmd", required=True)


    runp = sub.add_parser("run", help="Run full pipeline: load -> compile -> compare -> export")
    runp.add_argument("--config", required=True)


    args = ap.parse_args(argv)


    if args.cmd == "run":
        cfg = load_config(args.config)
        frames = _load_sources(cfg)
        compiled = _compile_all(cfg, frames)
        reports = _compare_all(cfg, compiled)
        exported = _export_all(cfg, compiled)


        # persist compare reports next to exports
        out_paths = []
        if exported:
            base = Path(exported[0]).parent
        else:
            base = Path.cwd() / "out"
        # for name, df in reports.items():
        #     path = base / f"{name}.csv"
        #     df.to_csv(path, index=False)
        #     out_paths.append(str(path))
        
        log.info(f"Done. Exported: {exported}; Reports: {out_paths}")
        return 0
    return 1

if __name__ == "__main__": # pragma: no cover
    raise SystemExit(main())