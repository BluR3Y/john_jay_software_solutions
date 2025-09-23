from __future__ import annotations
import json
import logging
from datetime import datetime
from .context import get_correlation_id

class TextFormatter(logging.Formatter):
    # Example: [2025-09-22T01:23:45.678Z] INFO data_manager.compile: message | corr=abc123
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.utcfromtimestamp(record.created).isoformat(timespec="milliseconds") + "Z"
        base = f"[{ts}] {record.levelname} {record.name}: {record.getMessage()}"
        corr = get_correlation_id()
        if corr:
            base += f" | corr={corr}"
        if record.exc_info:
            base += "\n" + self.formatException(record.exc_info)
        return base

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.utcfromtimestamp(record.created).isoformat(timespec="milliseconds")+"Z",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "corr": get_correlation_id() or None,
        }
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)

def build_formatter(style: str = "text") -> logging.Formatter:
    return JsonFormatter() if style == "json" else TextFormatter()
