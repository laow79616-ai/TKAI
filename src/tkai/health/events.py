"""Framework-neutral health events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import HealthStatus


@dataclass(frozen=True, slots=True)
class HealthEvent:
    """Immutable passive health state transition event."""

    provider: str
    event: str
    old_status: HealthStatus
    new_status: HealthStatus
    timestamp: datetime
    reason: str | None = None
