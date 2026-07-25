"""Structured local logging that removes common sensitive fields."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass

_SENSITIVE = ("password", "token", "secret", "credential", "authorization")


@dataclass(frozen=True, slots=True)
class LogEntry:
    """Immutable, JSON-safe structured log entry."""

    level: str
    event: str
    request_id: str | None
    fields: Mapping[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "level": self.level,
            "event": self.event,
            "request_id": self.request_id,
            "fields": dict(self.fields),
        }


class StructuredLogger:
    """Emit sanitized JSON log lines through an injected sink."""

    def __init__(
        self, level: str = "INFO", sink: Callable[[str], None] | None = None
    ) -> None:
        self._level = level
        self._sink = sink if sink is not None else print

    def log(
        self, level: str, event: str, *, request_id: str | None = None, **fields: object
    ) -> None:
        """Write a log line when its level meets the configured threshold."""
        if _level_value(level) < _level_value(self._level):
            return
        entry = LogEntry(level, event, request_id, _sanitize(fields))
        self._sink(json.dumps(entry.to_dict(), sort_keys=True, default=str))


def _level_value(level: str) -> int:
    return {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}[level]


def _sanitize(fields: Mapping[str, object]) -> dict[str, object]:
    return {
        key: "[REDACTED]" if any(word in key.lower() for word in _SENSITIVE) else value
        for key, value in sorted(fields.items())
    }
