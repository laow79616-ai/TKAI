"""Small in-memory metrics interface without a metrics server dependency."""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    """Stable count-only metrics snapshot."""

    counters: tuple[tuple[str, int], ...]

    def to_dict(self) -> dict[str, int]:
        return dict(self.counters)


class InMemoryMetrics:
    """Thread-safe local counters with no exporter or process-global state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._counters: dict[str, int] = {}

    def increment(self, name: str, amount: int = 1) -> None:
        """Increment a named local counter."""
        with self._lock:
            self._counters[name] = self._counters.get(name, 0) + amount

    def snapshot(self) -> MetricsSnapshot:
        """Return a deterministic immutable counter view."""
        with self._lock:
            return MetricsSnapshot(tuple(sorted(self._counters.items())))
