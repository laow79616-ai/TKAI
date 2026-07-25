"""Caller-driven startup, liveness, and readiness states."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True, slots=True)
class ProductionHealthSnapshot:
    """Immutable lifecycle health state without active dependency probes."""

    started: bool
    ready: bool
    live: bool

    def to_dict(self) -> dict[str, bool]:
        return {"started": self.started, "ready": self.ready, "live": self.live}


class ProductionHealth:
    """Maintain explicit lifecycle health states supplied by the application."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._started = False
        self._ready = False
        self._live = True

    def start(self) -> None:
        """Mark the application startup sequence complete and ready."""
        with self._lock:
            self._started = True
            self._ready = True

    def close(self) -> None:
        """Mark the application unready and no longer live."""
        with self._lock:
            self._ready = False
            self._live = False

    def snapshot(self) -> ProductionHealthSnapshot:
        """Return caller-driven lifecycle status."""
        with self._lock:
            return ProductionHealthSnapshot(self._started, self._ready, self._live)
