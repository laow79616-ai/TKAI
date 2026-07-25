"""Per-application lifecycle owner for local production-hardening components."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from threading import RLock

from .config import ProductionConfiguration
from .health import ProductionHealth
from .logging import StructuredLogger
from .metrics import InMemoryMetrics
from .rate_limit import InMemoryRateLimiter, RateLimiter


class ProductionRuntime:
    """Explicit runtime state; it never creates a process-wide singleton."""

    def __init__(
        self,
        configuration: ProductionConfiguration | None = None,
        *,
        rate_limiter: RateLimiter | None = None,
        closers: Iterable[Callable[[], None]] = (),
    ) -> None:
        self.configuration = configuration or ProductionConfiguration()
        self.logger = StructuredLogger(self.configuration.log_level)
        self.metrics = InMemoryMetrics()
        self.health = ProductionHealth()
        self.rate_limiter = rate_limiter or InMemoryRateLimiter(
            self.configuration.rate_limit_requests,
            self.configuration.rate_limit_window_seconds,
        )
        self._closers = tuple(closers)
        self._lock = RLock()
        self._closed = False

    def start(self) -> None:
        """Mark startup complete without launching a background task."""
        with self._lock:
            if not self._closed:
                self.health.start()

    def close(self) -> None:
        """Close injected resources once and publish a final health state."""
        with self._lock:
            if self._closed:
                return
            for closer in self._closers:
                closer()
            self.health.close()
            self._closed = True
