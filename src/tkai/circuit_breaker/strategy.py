"""Replaceable state-transition policy for circuit breakers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from .models import CircuitBreakerSnapshot


class CircuitBreakerStrategy(ABC):
    """Decide when a breaker may transition without owning breaker state."""

    @abstractmethod
    def should_open(self, snapshot: CircuitBreakerSnapshot) -> bool:
        """Return whether a closed breaker should open after a failure."""

    @abstractmethod
    def should_half_open(self, snapshot: CircuitBreakerSnapshot, now: datetime) -> bool:
        """Return whether an open breaker may admit a half-open probe."""

    @abstractmethod
    def should_close(self, snapshot: CircuitBreakerSnapshot) -> bool:
        """Return whether a half-open breaker should close after success."""


@dataclass(frozen=True, slots=True)
class ThresholdStrategy(CircuitBreakerStrategy):
    """Fixed-threshold default with configurable failures, duration, and probes."""

    failure_threshold: int = 5
    open_duration: timedelta = timedelta(seconds=30)
    half_open_success_threshold: int = 3

    def __post_init__(self) -> None:
        """Reject invalid thresholds before a breaker can use this strategy."""
        if self.failure_threshold < 1:
            raise ValueError("failure_threshold must be at least one")
        if self.open_duration.total_seconds() < 0:
            raise ValueError("open_duration must not be negative")
        if self.half_open_success_threshold < 1:
            raise ValueError("half_open_success_threshold must be at least one")

    def should_open(self, snapshot: CircuitBreakerSnapshot) -> bool:
        """Open after the configured number of consecutive failures."""
        return snapshot.consecutive_failures >= self.failure_threshold

    def should_half_open(self, snapshot: CircuitBreakerSnapshot, now: datetime) -> bool:
        """Allow one half-open probe once the configured open duration elapses."""
        return snapshot.opened_at is not None and now >= (
            snapshot.opened_at + self.open_duration
        )

    def should_close(self, snapshot: CircuitBreakerSnapshot) -> bool:
        """Close after the configured number of successful half-open probes."""
        return snapshot.half_open_success_count >= self.half_open_success_threshold
