"""Replaceable passive health evaluation."""

from __future__ import annotations

from dataclasses import dataclass

from .models import HealthSnapshot, HealthStatus


@dataclass(frozen=True, slots=True)
class HealthThresholds:
    degraded_failures: int = 2
    unhealthy_failures: int = 3


class HealthEvaluator:
    def __init__(self, thresholds: HealthThresholds | None = None) -> None:
        self.thresholds = thresholds or HealthThresholds()

    def evaluate(self, snapshot: HealthSnapshot) -> HealthStatus:
        if snapshot.statistics.requests == 0:
            return HealthStatus.UNKNOWN
        if snapshot.consecutive_failures >= self.thresholds.unhealthy_failures:
            return HealthStatus.UNHEALTHY
        if snapshot.consecutive_failures >= self.thresholds.degraded_failures:
            return HealthStatus.DEGRADED
        return HealthStatus.HEALTHY
