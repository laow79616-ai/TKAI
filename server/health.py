"""Offline, caller-driven Marketplace Server Health Foundation.

The original passive report contracts remain available for the Server V6
architecture.  The Foundation below adds only explicit, in-memory storage for
caller-provided checks and results; it never probes a dependency itself.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from types import MappingProxyType
from typing import Protocol


def _metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    """Create a stable defensive metadata mapping."""
    return MappingProxyType(dict(sorted(values.items())))


class HealthError(Exception):
    """Base error for explicit local Health Foundation operations."""


class HealthValidationError(HealthError):
    """Raised when a Health Foundation model is invalid."""


class HealthConflictError(HealthError):
    """Raised when an identifier already exists."""


class HealthNotFoundError(HealthError):
    """Raised when a requested check does not exist."""


class HealthClosedError(HealthError):
    """Raised when an operation is attempted after close."""


class HealthStatus(str, Enum):
    """Explicit current statuses plus legacy passive-report aliases."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    PASS = "pass"
    WARNING = "warning"
    ERROR = "error"


class HealthSeverity(str, Enum):
    """Descriptive severity supplied by a Health result caller."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class HealthEventType(str, Enum):
    """Stable local Health state event names."""

    CHECK_REGISTERED = "check_registered"
    CHECK_REMOVED = "check_removed"
    RESULT_UPDATED = "result_updated"
    CLEARED = "cleared"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True)
class HealthCheckId:
    """Immutable local Health check identifier."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise HealthValidationError("Health check identifier must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class HealthCheck:
    """Caller-registered check declaration; it does not execute a probe."""

    name: str
    status: HealthStatus = HealthStatus.UNKNOWN
    message: str = ""
    check_id: HealthCheckId | None = None
    severity: HealthSeverity = HealthSeverity.INFO
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise HealthValidationError("Health check name must not be empty.")
        object.__setattr__(self, "check_id", self.check_id or HealthCheckId(self.name))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "check_id": str(self.check_id),
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "severity": self.severity.value,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class HealthResult:
    """Caller-provided immutable result; no check is run by this module."""

    check_id: HealthCheckId
    status: HealthStatus
    severity: HealthSeverity = HealthSeverity.INFO
    message: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "check_id": str(self.check_id),
            "status": self.status.value,
            "severity": self.severity.value,
            "message": self.message,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class HealthReport:
    """Legacy passive report of explicitly supplied check declarations."""

    checks: tuple[HealthCheck, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "checks", tuple(sorted(self.checks, key=lambda item: item.name))
        )


@dataclass(frozen=True, slots=True)
class HealthStatistics:
    """Fresh status counts derived only from the in-memory current results."""

    total_checks: int = 0
    healthy: int = 0
    degraded: int = 0
    unhealthy: int = 0
    unknown: int = 0
    closed: bool = False

    def to_dict(self) -> dict[str, int | bool]:
        return {
            "total_checks": self.total_checks,
            "healthy": self.healthy,
            "degraded": self.degraded,
            "unhealthy": self.unhealthy,
            "unknown": self.unknown,
            "closed": self.closed,
        }


@dataclass(frozen=True, slots=True)
class HealthEvent:
    """Immutable deterministic event with no timestamp dependency."""

    sequence: int
    event_type: HealthEventType
    check_id: HealthCheckId | None = None
    count: int = 0

    def __post_init__(self) -> None:
        if self.sequence <= 0 or self.count < 0:
            raise HealthValidationError("Health event sequence and count are invalid.")

    def to_dict(self) -> dict[str, object]:
        return {
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "check_id": str(self.check_id) if self.check_id is not None else None,
            "count": self.count,
        }


@dataclass(frozen=True, slots=True)
class HealthSnapshot:
    """Stable immutable Health Foundation state, readable after close."""

    report: HealthReport = field(default_factory=HealthReport)
    checks: tuple[HealthCheck, ...] = ()
    results: tuple[HealthResult, ...] = ()
    events: tuple[HealthEvent, ...] = ()
    statistics: HealthStatistics = field(default_factory=HealthStatistics)
    closed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "checks", tuple(self.checks))
        object.__setattr__(self, "results", tuple(self.results))
        object.__setattr__(self, "events", tuple(self.events))

    def to_dict(self) -> dict[str, object]:
        return {
            "checks": [check.to_dict() for check in self.checks],
            "results": [result.to_dict() for result in self.results],
            "events": [event.to_dict() for event in self.events],
            "statistics": self.statistics.to_dict(),
            "closed": self.closed,
        }


class HealthStorage(Protocol):
    """Explicit storage boundary for caller-provided Health domain state."""

    def register_check(self, check: HealthCheck) -> HealthCheck: ...

    def unregister_check(self, check_id: HealthCheckId) -> HealthCheck: ...

    def update_result(self, result: HealthResult) -> HealthResult: ...

    def get_check(self, check_id: HealthCheckId) -> HealthCheck: ...

    def list_checks(self) -> tuple[HealthCheck, ...]: ...

    def snapshot(self) -> HealthSnapshot: ...

    def statistics(self) -> HealthStatistics: ...

    def events(self) -> tuple[HealthEvent, ...]: ...

    def record_event(self, event: HealthEvent) -> None: ...

    def clear(self) -> tuple[HealthCheck, ...]: ...

    def close(self) -> None: ...


class ReferenceHealthStorage:
    """Thread-safe, pure-memory storage; it does not perform health checks."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._checks: dict[str, HealthCheck] = {}
        self._results: dict[str, HealthResult] = {}
        self._events: list[HealthEvent] = []
        self._closed = False

    def register_check(self, check: HealthCheck) -> HealthCheck:
        with self._lock:
            self._ensure_open()
            identifier = str(check.check_id)
            if identifier in self._checks:
                raise HealthConflictError("Health check identifier already exists.")
            self._checks[identifier] = check
            return check

    def unregister_check(self, check_id: HealthCheckId) -> HealthCheck:
        with self._lock:
            self._ensure_open()
            check = self.get_check(check_id)
            del self._checks[str(check_id)]
            self._results.pop(str(check_id), None)
            return check

    def update_result(self, result: HealthResult) -> HealthResult:
        with self._lock:
            self._ensure_open()
            self.get_check(result.check_id)
            self._results[str(result.check_id)] = result
            return result

    def get_check(self, check_id: HealthCheckId) -> HealthCheck:
        with self._lock:
            self._ensure_open()
            try:
                return self._checks[str(check_id)]
            except KeyError as exc:
                raise HealthNotFoundError(str(check_id)) from exc

    def list_checks(self) -> tuple[HealthCheck, ...]:
        with self._lock:
            self._ensure_open()
            return self._checks_in_order()

    def statistics(self) -> HealthStatistics:
        """Calculate fresh counts, including after close, from supplied results."""
        with self._lock:
            statuses = [
                result.status if result is not None else HealthStatus.UNKNOWN
                for check in self._checks_in_order()
                for result in (self._results.get(str(check.check_id)),)
            ]
            return HealthStatistics(
                total_checks=len(self._checks),
                healthy=sum(status is HealthStatus.HEALTHY for status in statuses),
                degraded=sum(status is HealthStatus.DEGRADED for status in statuses),
                unhealthy=sum(status is HealthStatus.UNHEALTHY for status in statuses),
                unknown=sum(status is HealthStatus.UNKNOWN for status in statuses),
                closed=self._closed,
            )

    def snapshot(self) -> HealthSnapshot:
        """Return immutable, deterministic local state, including after close."""
        with self._lock:
            checks = self._checks_in_order()
            return HealthSnapshot(
                report=HealthReport(checks),
                checks=checks,
                results=tuple(self._results[key] for key in sorted(self._results)),
                events=tuple(self._events),
                statistics=self.statistics(),
                closed=self._closed,
            )

    def events(self) -> tuple[HealthEvent, ...]:
        with self._lock:
            return tuple(self._events)

    def record_event(self, event: HealthEvent) -> None:
        with self._lock:
            self._events.append(event)

    def clear(self) -> tuple[HealthCheck, ...]:
        with self._lock:
            self._ensure_open()
            checks = self._checks_in_order()
            self._checks.clear()
            self._results.clear()
            return checks

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _checks_in_order(self) -> tuple[HealthCheck, ...]:
        return tuple(self._checks[key] for key in sorted(self._checks))

    def _ensure_open(self) -> None:
        if self._closed:
            raise HealthClosedError("Reference Health storage is closed.")


class ReferenceHealthService:
    """Explicit local Health service; it accepts results but runs no probe."""

    def __init__(self, storage: HealthStorage | None = None) -> None:
        self._storage = storage if storage is not None else ReferenceHealthStorage()
        self._lock = RLock()
        self._sequence = 0
        self._closed = False

    def register_check(self, check: HealthCheck) -> HealthCheck:
        with self._lock:
            self._ensure_open()
            registered = self._storage.register_check(check)
            self._record(HealthEventType.CHECK_REGISTERED, check.check_id)
            return registered

    def unregister_check(self, check_id: HealthCheckId) -> HealthCheck:
        with self._lock:
            self._ensure_open()
            removed = self._storage.unregister_check(check_id)
            self._record(HealthEventType.CHECK_REMOVED, check_id)
            return removed

    def update_result(self, result: HealthResult) -> HealthResult:
        with self._lock:
            self._ensure_open()
            updated = self._storage.update_result(result)
            self._record(HealthEventType.RESULT_UPDATED, result.check_id)
            return updated

    def get_check(self, check_id: HealthCheckId) -> HealthCheck:
        with self._lock:
            self._ensure_open()
            return self._storage.get_check(check_id)

    def list_checks(self) -> tuple[HealthCheck, ...]:
        with self._lock:
            self._ensure_open()
            return self._storage.list_checks()

    def snapshot(self) -> HealthSnapshot:
        with self._lock:
            return self._storage.snapshot()

    def statistics(self) -> HealthStatistics:
        with self._lock:
            return self._storage.statistics()

    def events(self) -> tuple[HealthEvent, ...]:
        with self._lock:
            return self._storage.events()

    def clear(self) -> tuple[HealthCheck, ...]:
        with self._lock:
            self._ensure_open()
            checks = self._storage.clear()
            self._record(HealthEventType.CLEARED, count=len(checks))
            return checks

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._record(HealthEventType.CLOSED)
            self._storage.close()
            self._closed = True

    def _record(
        self,
        event_type: HealthEventType,
        check_id: HealthCheckId | None = None,
        count: int = 0,
    ) -> None:
        self._sequence += 1
        self._storage.record_event(
            HealthEvent(self._sequence, event_type, check_id, count)
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise HealthClosedError("Reference Health service is closed.")
