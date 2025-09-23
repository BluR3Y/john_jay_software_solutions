"""
wbm: A small library for reading, diffing, and writing Excel workbooks via pandas + openpyxl.

High-level API:
  - WorkbookManager: orchestrates file I/O and sheet registration
  - SheetManager: per-sheet operations, diffs, and annotations

CLI entry point: `wbm` (see wbm.cli:main).
"""
from .workbook_manager import WorkbookManager
from .sheet_manager import SheetManager
__all__ = ["WorkbookManager", "SheetManager"]
