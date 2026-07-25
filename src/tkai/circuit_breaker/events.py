"""Immutable circuit breaker state transition events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import CircuitState


@dataclass(frozen=True, slots=True)
class CircuitBreakerEvent:
    """One state transition emitted by a provider breaker."""

    provider: str
    event: str
    old_state: CircuitState
    new_state: CircuitState
    timestamp: datetime
    reason: str | None = None
