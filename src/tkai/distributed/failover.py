"""Explicit, opt-in automatic backend failover based on health probe snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum, IntEnum
from threading import Event, RLock, Thread, current_thread
from typing import Protocol

from tkai.observability import EventBus

from .backend import LocalMemoryBackend
from .errors import FailoverStateError
from .events import BackendFailedBack, BackendFailedOver, PrimaryBackendRecovered
from .health import (
    BackendHealthChecker,
    BackendHealthSnapshot,
    BackendHealthStatus,
    HealthChecker,
)


class FailoverBackend(Protocol):
    """Backend operations required by an explicit failover manager."""

    def connect(self) -> None: ...
    def probe_health(self, *, timeout_seconds: float | None = None) -> bool: ...


class BackendPriority(IntEnum):
    """Stable preference ordering for the configured primary and secondary."""

    PRIMARY = 0
    SECONDARY = 1


class FailoverState(str, Enum):
    """Validated state machine for explicit backend failover and failback."""

    PRIMARY_ACTIVE = "primary_active"
    SECONDARY_ACTIVE = "secondary_active"
    PRIMARY_RECOVERED = "primary_recovered"


@dataclass(frozen=True, slots=True)
class FailoverConfig:
    """Immutable thresholds and explicit periodic-monitor configuration."""

    failure_threshold: int = 3
    recovery_threshold: int = 3
    interval_seconds: float = 30.0

    def __post_init__(self) -> None:
        """Reject invalid thresholds before checking or connecting any backend."""
        if self.failure_threshold < 1:
            raise ValueError("Failover failure_threshold must be positive.")
        if self.recovery_threshold < 1:
            raise ValueError("Failover recovery_threshold must be positive.")
        if self.interval_seconds <= 0:
            raise ValueError("Failover interval_seconds must be greater than zero.")


@dataclass(frozen=True, slots=True)
class FailoverMetrics:
    """Immutable counters that make manager state observable without side effects."""

    evaluations: int = 0
    failovers: int = 0
    recoveries: int = 0
    failbacks: int = 0


@dataclass(frozen=True, slots=True)
class FailoverSnapshot:
    """Safe current failover state and recent primary health information."""

    state: FailoverState
    active_backend: str
    priority: BackendPriority
    consecutive_failures: int
    consecutive_recoveries: int
    last_transition: datetime | None
    primary_health: BackendHealthSnapshot | None
    metrics: FailoverMetrics

    def to_dict(self) -> dict[str, object]:
        """Return stable JSON-ready state without leaking backend client internals."""
        return {
            "state": self.state.value,
            "active_backend": self.active_backend,
            "priority": self.priority.name.lower(),
            "consecutive_failures": self.consecutive_failures,
            "consecutive_recoveries": self.consecutive_recoveries,
            "last_transition": (
                self.last_transition.isoformat() if self.last_transition else None
            ),
            "primary_health": (
                self.primary_health.to_dict() if self.primary_health else None
            ),
            "metrics": {
                "evaluations": self.metrics.evaluations,
                "failovers": self.metrics.failovers,
                "recoveries": self.metrics.recoveries,
                "failbacks": self.metrics.failbacks,
            },
        }


class FailoverManager:
    """Opt-in manager that fails over after health thresholds are reached.

    The manager is never attached automatically to a coordinator, Runtime, or
    ProviderManager. It does not close caller-provided backends, and recovered
    primaries require an explicit :meth:`manual_failback` to become active.
    """

    def __init__(
        self,
        primary: FailoverBackend,
        secondary: FailoverBackend | None = None,
        *,
        config: FailoverConfig | None = None,
        health_checker: HealthChecker | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Configure a primary and local-memory fallback without starting probes."""
        self.primary = primary
        self.secondary = secondary or LocalMemoryBackend()
        self.config = config or FailoverConfig()
        self._health_checker = health_checker or BackendHealthChecker(primary)
        self._event_bus = event_bus
        self._lock = RLock()
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._state = FailoverState.PRIMARY_ACTIVE
        self._consecutive_failures = 0
        self._consecutive_recoveries = 0
        self._last_transition: datetime | None = None
        self._primary_health: BackendHealthSnapshot | None = None
        self._metrics = FailoverMetrics()

    @property
    def active_backend(self) -> FailoverBackend:
        """Return the currently selected backend without changing lifecycle state."""
        with self._lock:
            return (
                self.primary
                if self._state is FailoverState.PRIMARY_ACTIVE
                else self.secondary
            )

    def evaluate(self) -> FailoverSnapshot:
        """Probe the primary once and apply only validated state transitions."""
        health = self._health_checker.probe()
        event: BackendFailedOver | PrimaryBackendRecovered | None = None
        with self._lock:
            self._primary_health = health
            self._metrics = FailoverMetrics(
                evaluations=self._metrics.evaluations + 1,
                failovers=self._metrics.failovers,
                recoveries=self._metrics.recoveries,
                failbacks=self._metrics.failbacks,
            )
            if self._state is FailoverState.PRIMARY_ACTIVE:
                if health.status is BackendHealthStatus.HEALTHY:
                    self._consecutive_failures = 0
                else:
                    self._consecutive_failures += 1
                    if self._consecutive_failures >= self.config.failure_threshold:
                        self.secondary.connect()
                        self._transition(FailoverState.SECONDARY_ACTIVE)
                        self._metrics = FailoverMetrics(
                            evaluations=self._metrics.evaluations,
                            failovers=self._metrics.failovers + 1,
                            recoveries=self._metrics.recoveries,
                            failbacks=self._metrics.failbacks,
                        )
                        event = BackendFailedOver(subject=type(self.secondary).__name__)
            elif self._state is FailoverState.SECONDARY_ACTIVE:
                if health.status is BackendHealthStatus.HEALTHY:
                    self._consecutive_recoveries += 1
                    if self._consecutive_recoveries >= self.config.recovery_threshold:
                        self._transition(FailoverState.PRIMARY_RECOVERED)
                        self._metrics = FailoverMetrics(
                            evaluations=self._metrics.evaluations,
                            failovers=self._metrics.failovers,
                            recoveries=self._metrics.recoveries + 1,
                            failbacks=self._metrics.failbacks,
                        )
                        event = PrimaryBackendRecovered(
                            subject=type(self.primary).__name__
                        )
                else:
                    self._consecutive_recoveries = 0
            snapshot = self._snapshot_locked()
        self._publish(event)
        return snapshot

    def manual_failback(self) -> FailoverSnapshot:
        """Activate a recovered primary; invalid state requests raise clearly."""
        with self._lock:
            if self._state is not FailoverState.PRIMARY_RECOVERED:
                raise FailoverStateError(
                    "Manual failback requires a recovered primary backend."
                )
            self.primary.connect()
            self._transition(FailoverState.PRIMARY_ACTIVE)
            self._consecutive_failures = 0
            self._consecutive_recoveries = 0
            self._metrics = FailoverMetrics(
                evaluations=self._metrics.evaluations,
                failovers=self._metrics.failovers,
                recoveries=self._metrics.recoveries,
                failbacks=self._metrics.failbacks + 1,
            )
            snapshot = self._snapshot_locked()
        self._publish(BackendFailedBack(subject=type(self.primary).__name__))
        return snapshot

    def snapshot(self) -> FailoverSnapshot:
        """Return an immutable diagnostic snapshot without probing a backend."""
        with self._lock:
            return self._snapshot_locked()

    def start(self) -> None:
        """Start one explicit periodic evaluation worker; calls are idempotent."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = Thread(
                target=self._run_periodically,
                name="tkai-backend-failover",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Stop the manager's worker without closing either supplied backend."""
        with self._lock:
            thread = self._thread
            self._thread = None
            self._stop_event.set()
        if thread is not None and thread is not current_thread():
            thread.join(timeout=self.config.interval_seconds)

    close = stop

    def _run_periodically(self) -> None:
        self.evaluate()
        while not self._stop_event.wait(self.config.interval_seconds):
            self.evaluate()

    def _transition(self, state: FailoverState) -> None:
        """Apply a transition only if it is legal in the explicit state machine."""
        valid = {
            FailoverState.PRIMARY_ACTIVE: {FailoverState.SECONDARY_ACTIVE},
            FailoverState.SECONDARY_ACTIVE: {FailoverState.PRIMARY_RECOVERED},
            FailoverState.PRIMARY_RECOVERED: {FailoverState.PRIMARY_ACTIVE},
        }
        if state not in valid[self._state]:
            raise FailoverStateError(
                f"Cannot transition from {self._state.value} to {state.value}."
            )
        self._state = state
        self._last_transition = datetime.now(timezone.utc)

    def _snapshot_locked(self) -> FailoverSnapshot:
        priority = (
            BackendPriority.PRIMARY
            if self._state is FailoverState.PRIMARY_ACTIVE
            else BackendPriority.SECONDARY
        )
        active = self.primary if priority is BackendPriority.PRIMARY else self.secondary
        return FailoverSnapshot(
            self._state,
            type(active).__name__,
            priority,
            self._consecutive_failures,
            self._consecutive_recoveries,
            self._last_transition,
            self._primary_health,
            self._metrics,
        )

    def _publish(
        self,
        event: BackendFailedOver | PrimaryBackendRecovered | BackendFailedBack | None,
    ) -> None:
        if event is not None and self._event_bus is not None:
            try:
                self._event_bus.publish(event)
            except Exception:
                return
