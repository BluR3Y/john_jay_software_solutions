from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
from jsonschema import validate, Draft202012Validator
from jsonschema.exceptions import ValidationError


from .exceptions import ConfigError
from .models import Config

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

def load_config(path: str | Path) -> Config:
    p = Path(path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise ConfigError(f"Failed to read config: {e}")
    
    # Validate
    try:
        Draft202012Validator(_SCHEMA).validate(data)
    except ValidationError as e:
        raise ConfigError(_friendly_error(e))
    
    return Config(raw=data)