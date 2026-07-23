"""Immutable, JSON-safe telemetry data models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class MetricKind(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass(frozen=True, slots=True)
class Metric:
    name: str
    value: float
    unit: str = "count"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    labels: dict[str, str] = field(default_factory=dict)
    kind: MetricKind = MetricKind.GAUGE

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["kind"] = self.kind.value
        data["timestamp"] = self.timestamp.astimezone(timezone.utc).isoformat()
        return data


@dataclass(frozen=True, slots=True)
class TraceContext:
    trace_id: str
    span_id: str
    parent_span_id: str | None
    operation: str
    started_at: datetime
    ended_at: datetime | None = None
    status: str = "running"
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["started_at"] = self.started_at.astimezone(timezone.utc).isoformat()
        data["ended_at"] = (
            self.ended_at.astimezone(timezone.utc).isoformat()
            if self.ended_at
            else None
        )
        return data


@dataclass(frozen=True, slots=True)
class StructuredLog:
    timestamp: datetime
    level: str
    message: str
    trace_id: str | None = None
    correlation_id: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    span_id: str | None = None

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["timestamp"] = self.timestamp.astimezone(timezone.utc).isoformat()
        return data
