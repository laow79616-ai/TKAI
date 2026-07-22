"""Framework-neutral health events."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import HealthStatus


@dataclass(frozen=True, slots=True)
class HealthEvent:
    provider: str
    event: str
    status: HealthStatus
    timestamp: datetime
