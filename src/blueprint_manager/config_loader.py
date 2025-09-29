from __future__ import annotations
import json, glob, os
import re
from pathlib import Path
from typing import Any, Dict, Tuple
from jsonschema import validate, Draft202012Validator
from jsonschema.exceptions import ValidationError


from .exceptions import ConfigError
from .models import Config

_VAR = re.compile(r"\$\{([^}]+)\}")

# Lists under these key-paths will be appended (others still replace)
APPEND_LIST_KEYS: set[Tuple[str, ...]] = {
    ("sources",),
    ("compile", "targets"),
    ("compare", "pairs"),
    ("export", "workbooks"),
}

_SCHEMA: Dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": [
        "schema",
        "sources",
        "compile"
    ],
    "properties": {
        "version": {
            "type": [
                "string",
                "number"
            ]
        },
        "timezone": {
            "type": [
                "string",
                "null"
            ]
        },
        "output": {
            "type": [
                "string",
                "null"
            ]
        },
        "schema": {
            "type": "object",
            "properties": {
                "aliases": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "enum": [
                                    "string",
                                    "integer",
                                    "number",
                                    "date",
                                    "boolean"
                                ]
                            },
                            "identifier": {
                                "type": "boolean"
                            },
                            "not_null": {
                                "type": "boolean"
                            },
                            "enum": {
                                "type": "array",
                                "items": {
                                    "type": "string"
                                }
                            },
                            "date": {
                                "type": "object",
                                "properties": {
                                    "format": {
                                        "type": "string"
                                    },
                                    "granularity": {
                                        "type": "string"
                                    },
                                    "abs_tol": {
                                        "type": "string"
                                    }
                                },
                                "required": [
                                    "format"
                                ],
                                "additionalProperties": True
                            }
                        },
                        "required": [
                            "type"
                        ],
                        "additionalProperties": True
                    }
                }
            },
            "required": [
                "aliases"
            ]
        },
        "sources": {
            "type": "array"
        },
        "compile": {
            "type": "object"
        },
        "compare": {
            "type": "object"
        },
        "export": {
            "type": "object"
        }
    }
}

def _friendly_error(err: ValidationError) -> str:
    loc = " / ".join(str(p) for p in err.path)
    what = err.message
    return f"Config validation error at `{loc or '<root>'}`: {what}"

def deep_merge(a, b, path: tuple[str, ...] = ()):
    # handle None
    if a is None: return b
    if b is None: return a

    # dicts → recursive merge
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = deep_merge(out.get(k), v, path + (k,))
        return out

    # lists → append for specific paths, else replace
    if isinstance(a, list) and isinstance(b, list):
        if path in APPEND_LIST_KEYS:
            return a + b
        return b  # replace-by-default elsewhere

    # scalars → override
    return b

def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def load_config_file(path: Path) -> dict:
    raw = _read_json(path)
    raw = _expand_includes(path.parent, raw)
    return raw

def _expand_includes(base_dir: Path, data: dict, seen: set[str] | None = None) -> dict:
    if seen is None:
        seen = set()

    includes = data.pop("include", [])
    merged: dict = {}

    def _include_one(pattern: str):
        # resolve pattern relative to including file
        abs_pattern = (base_dir / pattern)
        # sorted for determinism
        for p in sorted(glob.glob(str(abs_pattern))):
            ap = str(Path(p).resolve())
            if ap in seen:
                # prevent include cycles
                continue
            seen.add(ap)
            inc = load_config_file(Path(p))  # this will call _expand_includes recursively
            nonlocal merged
            merged = deep_merge(merged, inc)

    if isinstance(includes, list):
        for inc in includes:
            _include_one(inc)
    elif includes:
        _include_one(includes)

    return deep_merge(merged, data)

def _get_by_path(d: dict, dotted: str):
    cur = d
    for part in dotted.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(f"$ref not found: {dotted}")
        cur = cur[part]
    return cur

def _resolve_refs(obj, root):
    if isinstance(obj, dict):
        if "$ref" in obj and len(obj) == 1:
            return _resolve_refs(_get_by_path(root, obj["$ref"]), root)
        return {k: _resolve_refs(v, root) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_resolve_refs(x, root) for x in obj]
    return obj

def _interp(value: str, ctx: dict):
    def repl(m):
        key = m.group(1)
        if "." in key:
            # config path
            try:
                return str(_get_by_path(ctx, key))
            except Exception:
                return os.getenv(key, m.group(0))
        return os.getenv(key, m.group(0))
    return _VAR.sub(repl, value)

def _interpolate(obj, ctx):
    if isinstance(obj, str):
        return _interp(obj, ctx)
    if isinstance(obj, list):
        return [_interpolate(x, ctx) for x in obj]
    if isinstance(obj, dict):
        return {k: _interpolate(v, ctx) for k, v in obj.items()}
    return obj


def load_config(entry: str, profile: str | None = None) -> Config:
    base = load_config_file(Path(entry))
    # optional profile
    if profile:
        prof_path = Path(entry).parent / "profiles" / f"{profile}.json"
        if prof_path.exists():
            base = deep_merge(base, load_config_file(prof_path))

    # resolve refs & interpolate (do refs first, then vars)
    resolved = _resolve_refs(base, base)
    resolved = _interpolate(resolved, resolved)

    # Validate
    try:
        Draft202012Validator(_SCHEMA).validate(resolved)
    except ValidationError as e:
        raise ConfigError(_friendly_error(e))

    return Config(raw=resolved)