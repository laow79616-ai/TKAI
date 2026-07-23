"""Thread-safe registry of explicitly supplied coordinator resource objects."""

from __future__ import annotations

from threading import RLock


class DistributedRegistry:
    """Store optional health/cache/retry/rate/plugin resources by stable name."""

    def __init__(self) -> None:
        self._resources: dict[str, object] = {}
        self._lock = RLock()

    def register(self, name: str, resource: object) -> None:
        """Register or replace an application-owned optional resource."""
        if not name:
            raise ValueError("resource name must not be empty")
        with self._lock:
            self._resources[name] = resource

    def get(self, name: str) -> object | None:
        """Return a resource without creating or activating it."""
        with self._lock:
            return self._resources.get(name)

    def list(self) -> list[str]:
        """Return stable registered resource names."""
        with self._lock:
            return sorted(self._resources)

    def clear(self) -> None:
        """Forget references without stopping caller-owned resources."""
        with self._lock:
            self._resources.clear()
