"""Typed passive runtime health models."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class HealthStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class HealthStatistics:
    requests: int = 0
    success: int = 0
    failure: int = 0
    timeout: int = 0


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    provider: str
    status: HealthStatus = HealthStatus.UNKNOWN
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    consecutive_failures: int = 0
    last_success: datetime | None = None
    last_failure: datetime | None = None
    last_update: datetime | None = None

    @property
    def statistics(self) -> HealthStatistics:
        return HealthStatistics(
            self.success_count + self.failure_count,
            self.success_count,
            self.failure_count,
            self.timeout_count,
        )
