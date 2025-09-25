# src/data_manager/plugins.py
from __future__ import annotations
from typing import Dict, Callable
import logging

logger = logging.getLogger("data_manager")

def _load_entrypoints(group: str) -> Dict[str, Callable]:
    try:
        # Python 3.10+: importlib.metadata is stdlib
        from importlib.metadata import entry_points
        eps = entry_points()
        # support both old/new APIs
        candidates = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])
        return {ep.name: ep.load() for ep in candidates}
    except Exception as e:
        logger.warning(f"Failed to load entry points for {group}: {e}")
        return {}

TRANSFORM_PLUGINS = _load_entrypoints("data_manager.transforms")
EXPR_OP_PLUGINS   = _load_entrypoints("data_manager.expr_ops")
ENRICH_PLUGINS    = _load_entrypoints("data_manager.enrich")
