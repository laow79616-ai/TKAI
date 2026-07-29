"""Local observability hooks with secret-safe structured output."""

from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TextIO

MetricHook = Callable[[str, float, Mapping[str, str]], None]
TraceHook = Callable[[str, Mapping[str, object]], None]
HealthCheck = Callable[[], bool]
AuditHook = Callable[["AuditRecord"], None]


@dataclass(frozen=True)
class AuditRecord:
    """Security-relevant action record."""

    action: str
    actor: str
    outcome: str
    details: Mapping[str, object] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ObservabilityRegistry:
    """Registers hooks without selecting a vendor or exporter."""

    def __init__(self) -> None:
        self.metrics: list[MetricHook] = []
        self.traces: list[TraceHook] = []
        self.health: dict[str, HealthCheck] = {}
        self.audit: list[AuditHook] = []

    def register_metric(self, hook: MetricHook) -> None:
        self.metrics.append(hook)

    def register_trace(self, hook: TraceHook) -> None:
        self.traces.append(hook)

    def register_health(self, name: str, check: HealthCheck) -> None:
        if name in self.health:
            raise ValueError(f"health check {name!r} already registered")
        self.health[name] = check

    def register_audit(self, hook: AuditHook) -> None:
        self.audit.append(hook)


class StructuredLogger:
    """Writes newline-delimited JSON after applying a secret filter."""

    def __init__(
        self,
        stream: TextIO,
        filter_values: Callable[[Mapping[str, object]], dict[str, object]],
    ) -> None:
        self._stream = stream
        self._filter_values = filter_values

    def log(self, level: str, message: str, **fields: object) -> None:
        record: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "message": message,
            **fields,
        }
        self._stream.write(json.dumps(self._filter_values(record), default=str) + "\n")


__all__ = (
    "AuditHook",
    "AuditRecord",
    "HealthCheck",
    "MetricHook",
    "ObservabilityRegistry",
    "StructuredLogger",
    "TraceHook",
)
