from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict, is_dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any, TextIO


def _serialize(value: Any) -> Any:
    if is_dataclass(value):
        return _serialize(asdict(value))
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize(item) for item in value]
    return value


class JsonLogger:
    def __init__(
        self,
        stream: TextIO | None = None,
        log_path: Path | None = None,
        stream_include_events: set[str] | None = None,
    ) -> None:
        self._stream = stream if stream is not None else sys.stdout
        self._file = None
        self._stream_include_events = stream_include_events
        if log_path is not None:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            self._file = log_path.open("a", encoding="utf-8")

    def close(self) -> None:
        if self._file is not None:
            self._file.close()
            self._file = None

    def emit(self, event: str, **fields: Any) -> None:
        payload = {
            "ts_ms": int(time.time() * 1000),
            "event": event,
            **{key: _serialize(value) for key, value in fields.items()},
        }
        line = json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        if self._stream_include_events is None or event in self._stream_include_events:
            self._stream.write(line + "\n")
            self._stream.flush()
        if self._file is not None:
            self._file.write(line + "\n")
            self._file.flush()
