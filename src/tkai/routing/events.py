"""Immutable routing events reserved for opt-in event bus integration."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from .models import RoutingDecision


@dataclass(frozen=True, slots=True)
class RoutingEvent:
    """Record an immutable routing decision without invoking providers."""

    decision: RoutingDecision
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
