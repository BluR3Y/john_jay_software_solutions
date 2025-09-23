from __future__ import annotations
import os
from pathlib import Path

def resolve_output_dir(config_out: str | None) -> Path:
    if not config_out:
        return Path.cwd() / "out"
    expanded = os.path.expandvars(config_out)
    return Path(expanded)