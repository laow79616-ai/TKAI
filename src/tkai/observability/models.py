"""Immutable observability event models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class Event:
    """Base immutable event emitted by framework-neutral observability code."""

    name: str = "Event"
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    trace_id: str | None = None
    correlation_id: str | None = None
    data: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class TraceContext:
    trace_id: str
    span_id: str
    duration: float | None = None
    parent_span_id: str | None = None
