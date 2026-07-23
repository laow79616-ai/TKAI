"""Explicit active health probes for distributed backends.

The checker is deliberately separate from backend ``health()`` methods.  The
latter retain their historical passive lifecycle meaning; probing is opt-in and
only starts periodic activity when callers explicitly invoke ``start()``.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from threading import Event, RLock, Thread, current_thread
from typing import Protocol


class BackendHealthStatus(str, Enum):
    """Result states for an explicit backend availability probe."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True, slots=True)
class BackendHealthSnapshot:
    """Immutable cached state from the most recent backend probe."""

    backend: str
    status: BackendHealthStatus
    last_probe: datetime | None = None
    last_error: str | None = None
    consecutive_failures: int = 0
    attempts: int = 0

    def to_dict(self) -> dict[str, object]:
        """Return a stable, JSON-ready view that excludes backend internals."""
        return {
            "backend": self.backend,
            "status": self.status.value,
            "last_probe": self.last_probe.isoformat() if self.last_probe else None,
            "last_error": self.last_error,
            "consecutive_failures": self.consecutive_failures,
            "attempts": self.attempts,
        }


@dataclass(frozen=True, slots=True)
class HealthProbeConfig:
    """Immutable, bounded configuration for manual or periodic probes."""

    interval_seconds: float = 30.0
    timeout_seconds: float = 5.0
    retries: int = 1
    degraded_after_failures: int = 1
    unhealthy_after_failures: int = 3

    def __post_init__(self) -> None:
        """Validate values without starting a thread or touching a backend."""
        if self.interval_seconds <= 0:
            raise ValueError("Health probe interval_seconds must be greater than zero.")
        if self.timeout_seconds <= 0:
            raise ValueError("Health probe timeout_seconds must be greater than zero.")
        if self.retries < 0:
            raise ValueError("Health probe retries must not be negative.")
        if self.degraded_after_failures < 1:
            raise ValueError("Health probe degraded_after_failures must be positive.")
        if self.unhealthy_after_failures < self.degraded_after_failures:
            raise ValueError(
                "Health probe unhealthy_after_failures must not be lower than "
                "degraded_after_failures."
            )


class ProbeableBackend(Protocol):
    """Small extension implemented by backends that support active probing."""

    def probe_health(self, *, timeout_seconds: float | None = None) -> bool: ...


class HealthChecker(Protocol):
    """Public contract for synchronous and asynchronous backend health checks."""

    def probe(self) -> BackendHealthSnapshot: ...
    async def aprobe(self) -> BackendHealthSnapshot: ...
    def snapshot(self) -> BackendHealthSnapshot: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...


class BackendHealthChecker:
    """Thread-safe explicit health checker with optional periodic probes.

    Probe retries are immediate and bounded.  This avoids hidden sleeping and
    keeps deterministic offline tests possible; transport-level timeout behavior
    remains the responsibility of each backend client.
    """

    def __init__(
        self,
        backend: ProbeableBackend,
        *,
        config: HealthProbeConfig | None = None,
    ) -> None:
        """Create a stopped checker and seed its safe cached snapshot."""
        self._backend = backend
        self.config = config or HealthProbeConfig()
        self._lock = RLock()
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._consecutive_failures = 0
        self._attempts = 0
        self._snapshot = BackendHealthSnapshot(
            type(backend).__name__, BackendHealthStatus.UNHEALTHY
        )

    def probe(self) -> BackendHealthSnapshot:
        """Run one bounded active probe and update the immutable cached result."""
        with self._lock:
            backend = self._backend
        error: Exception | None = None
        for _ in range(self.config.retries + 1):
            try:
                if backend.probe_health(timeout_seconds=self.config.timeout_seconds):
                    return self._record_success(backend)
                error = RuntimeError("Backend probe returned an unhealthy result.")
            except Exception as caught:
                error = caught
        return self._record_failure(backend, error)

    async def aprobe(self) -> BackendHealthSnapshot:
        """Run a synchronous backend probe without blocking an async caller."""
        return await asyncio.to_thread(self.probe)

    def snapshot(self) -> BackendHealthSnapshot:
        """Return the last immutable probe result without triggering a probe."""
        with self._lock:
            return self._snapshot

    def switch_backend(self, backend: ProbeableBackend) -> None:
        """Select a new backend explicitly and discard stale health cache state."""
        with self._lock:
            self._backend = backend
            self._consecutive_failures = 0
            self._attempts = 0
            self._snapshot = BackendHealthSnapshot(
                type(backend).__name__, BackendHealthStatus.UNHEALTHY
            )

    def start(self) -> None:
        """Start one daemon periodic worker; repeated calls are idempotent."""
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = Thread(
                target=self._run_periodically,
                name="tkai-backend-health-probe",
                daemon=True,
            )
            self._thread.start()

    def stop(self) -> None:
        """Stop and join the explicit periodic worker without closing its backend."""
        with self._lock:
            thread = self._thread
            self._thread = None
            self._stop_event.set()
        if thread is not None and thread is not current_thread():
            thread.join(timeout=self.config.timeout_seconds)

    close = stop

    def _run_periodically(self) -> None:
        """Probe immediately, then wait cooperatively between bounded intervals."""
        self.probe()
        while not self._stop_event.wait(self.config.interval_seconds):
            self.probe()

    def _record_success(self, backend: ProbeableBackend) -> BackendHealthSnapshot:
        with self._lock:
            self._consecutive_failures = 0
            self._attempts += 1
            self._snapshot = BackendHealthSnapshot(
                type(backend).__name__,
                BackendHealthStatus.HEALTHY,
                datetime.now(timezone.utc),
                None,
                self._consecutive_failures,
                self._attempts,
            )
            return self._snapshot

    def _record_failure(
        self, backend: ProbeableBackend, error: Exception | None
    ) -> BackendHealthSnapshot:
        with self._lock:
            self._consecutive_failures += 1
            self._attempts += 1
            status = (
                BackendHealthStatus.UNHEALTHY
                if self._consecutive_failures >= self.config.unhealthy_after_failures
                else (
                    BackendHealthStatus.DEGRADED
                    if self._consecutive_failures >= self.config.degraded_after_failures
                    else BackendHealthStatus.HEALTHY
                )
            )
            self._snapshot = BackendHealthSnapshot(
                type(backend).__name__,
                status,
                datetime.now(timezone.utc),
                type(error).__name__ if error is not None else "ProbeError",
                self._consecutive_failures,
                self._attempts,
            )
            return self._snapshot
