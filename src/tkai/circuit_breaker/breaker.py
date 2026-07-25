"""Thread-safe circuit breaker with a private, strategy-driven state machine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timezone
from threading import RLock

from .events import CircuitBreakerEvent
from .models import CircuitBreakerSnapshot, CircuitState
from .strategy import CircuitBreakerStrategy, ThresholdStrategy

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    """Return the default timezone-aware clock value."""
    return datetime.now(timezone.utc)


class CircuitBreaker:
    """Own mutable breaker mechanics while exposing immutable state snapshots."""

    def __init__(
        self,
        provider: str,
        *,
        strategy: CircuitBreakerStrategy | None = None,
        clock: Clock = _utc_now,
    ) -> None:
        if not provider:
            raise ValueError("provider must not be empty")
        self.provider = provider
        self.strategy = strategy or ThresholdStrategy()
        self._clock = clock
        self._snapshot = CircuitBreakerSnapshot(provider)
        self._lock = RLock()
        self.events: list[CircuitBreakerEvent] = []

    @property
    def snapshot(self) -> CircuitBreakerSnapshot:
        """Return the current immutable breaker state."""
        with self._lock:
            return self._snapshot

    def allow_request(self) -> bool:
        """Return whether a request may proceed and advance OPEN to HALF_OPEN."""
        with self._lock:
            snapshot = self._snapshot
            if snapshot.state is CircuitState.OPEN:
                now = self._clock()
                if not self.strategy.should_half_open(snapshot, now):
                    return False
                self._transition(CircuitState.HALF_OPEN, now, "open duration elapsed")
            return True

    def record_failure(self, *, reason: str | None = None) -> CircuitBreakerSnapshot:
        """Record one passive failure and open immediately from HALF_OPEN."""
        with self._lock:
            now = self._clock()
            snapshot = replace(
                self._snapshot,
                failure_count=self._snapshot.failure_count + 1,
                consecutive_failures=self._snapshot.consecutive_failures + 1,
                half_open_success_count=0,
                last_failure=now,
            )
            self._snapshot = snapshot
            if snapshot.state is CircuitState.HALF_OPEN or self.strategy.should_open(
                snapshot
            ):
                self._transition(
                    CircuitState.OPEN, now, reason or "failure threshold met"
                )
            return self._snapshot

    def record_success(self) -> CircuitBreakerSnapshot:
        """Record one passive success and close only after the probe threshold."""
        with self._lock:
            now = self._clock()
            increment = int(self._snapshot.state is CircuitState.HALF_OPEN)
            self._snapshot = replace(
                self._snapshot,
                success_count=self._snapshot.success_count + 1,
                consecutive_failures=0,
                half_open_success_count=self._snapshot.half_open_success_count
                + increment,
                last_success=now,
            )
            if (
                self._snapshot.state is CircuitState.HALF_OPEN
                and self.strategy.should_close(self._snapshot)
            ):
                self._transition(
                    CircuitState.CLOSED, now, "half-open success threshold met"
                )
            return self._snapshot

    def force_open(self, *, reason: str | None = None) -> CircuitBreakerSnapshot:
        """Open on an authoritative passive health event without a network probe."""
        with self._lock:
            self._transition(CircuitState.OPEN, self._clock(), reason or "health event")
            return self._snapshot

    def reset(self) -> CircuitBreakerSnapshot:
        """Reset all state through the state machine and retain a reset event."""
        with self._lock:
            old = self._snapshot
            self._snapshot = CircuitBreakerSnapshot(self.provider)
            self.events.append(
                CircuitBreakerEvent(
                    self.provider,
                    "BreakerReset",
                    old.state,
                    CircuitState.CLOSED,
                    self._clock(),
                )
            )
            return self._snapshot

    def _transition(
        self, state: CircuitState, now: datetime, reason: str | None
    ) -> None:
        """Apply all state changes in one private transition point."""
        old = self._snapshot
        if old.state is state:
            return
        if state is CircuitState.OPEN:
            self._snapshot = replace(
                old,
                state=state,
                opened_at=now,
                half_open_since=None,
                half_open_success_count=0,
            )
            event_name = "BreakerOpened"
        elif state is CircuitState.HALF_OPEN:
            self._snapshot = replace(
                old,
                state=state,
                half_open_since=now,
                half_open_success_count=0,
            )
            event_name = "BreakerHalfOpen"
        else:
            self._snapshot = replace(
                old,
                state=state,
                opened_at=None,
                half_open_since=None,
                half_open_success_count=0,
            )
            event_name = "BreakerClosed"
        self.events.append(
            CircuitBreakerEvent(
                self.provider, event_name, old.state, state, now, reason
            )
        )
