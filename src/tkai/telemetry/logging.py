"""Safe structured logging adapter that redacts common credential fields."""

from __future__ import annotations

from datetime import datetime, timezone
from threading import RLock
from typing import Any

from .context import CorrelationContext
from .models import StructuredLog

_SENSITIVE = {"api_key", "authorization", "token", "password", "secret"}


def _redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: "***" if key.lower() in _SENSITIVE else _redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_redact(item) for item in value]
    return value


class TelemetryLoggingAdapter:
    def __init__(self) -> None:
        self.records: list[StructuredLog] = []
        self._lock = RLock()

    def log(
        self,
        level: str,
        message: str,
        *,
        context: CorrelationContext | None = None,
        attributes: dict[str, Any] | None = None,
    ) -> StructuredLog:
        safe = _redact(attributes or {})
        record = StructuredLog(
            datetime.now(timezone.utc),
            level,
            message,
            context.trace_id if context else None,
            context.correlation_id if context else None,
            safe,
        )
        with self._lock:
            self.records.append(record)
        return record
