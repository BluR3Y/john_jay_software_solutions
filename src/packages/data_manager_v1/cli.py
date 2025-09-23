from __future__ import annotations
import argparse, json, sys, os
from .runner import run_with_config
from .io.loader import AdapterRegistry
try:
    # Optional: user may inject their managers by making them importable
    from workbook_manager import WorkbookManager  # type: ignore
except Exception:
    WorkbookManager = None  # type: ignore
try:
    from db_manager import AccessDbManager  # type: ignore
except Exception:
    AccessDbManager = None  # type: ignore

def main(argv=None):
    parser = argparse.ArgumentParser(prog="data_manager", description="data_manager runner")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_run = sub.add_parser("run", help="Run pipeline from config.json")
    p_run.add_argument("config", help="Path to config JSON")
    p_run.add_argument("--no-snapshots", action="store_true", help="Disable snapshot write")
    p_run.add_argument("--no-reports", action="store_true", help="Disable report write")
    p_run.add_argument("--inject-wbm", action="store_true", help="Inject WorkbookManager if available")
    p_run.add_argument("--inject-dbm", action="store_true", help="Inject AccessDbManager if available")
    args = parser.parse_args(argv)

    if args.cmd == "run":
        with open(args.config, "r", encoding="utf-8") as f:
            cfg = json.load(f)

        registry_kwargs = {}
        if args.inject_wbm and WorkbookManager is not None:
            registry_kwargs["workbook_manager"] = WorkbookManager()
        if args.inject_dbm and AccessDbManager is not None:
            registry_kwargs["db_manager"] = AccessDbManager()

        result = run_with_config(cfg, registry_kwargs=registry_kwargs,
                                 write_snapshots=not args.no_snapshots,
                                 write_reports=not args.no_reports)
        # Print a tiny summary
        compiled = result.get("compiled", {})
        for name, df in compiled.items():
            print(f"[compiled] {name}: {len(df)} rows")
        print("[ok]")

if __name__ == "__main__":
    main()