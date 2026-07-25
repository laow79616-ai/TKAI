"""Thread-safe registry for named cache backend instances."""

from __future__ import annotations

from threading import RLock

from .backend import CacheBackend
from .errors import CacheBackendNotFoundError, CacheError


class CacheRegistry:
    """Maintain the one backend collection used by cache manager facades."""

    def __init__(self) -> None:
        self._backends: dict[str, CacheBackend] = {}
        self._lock = RLock()

    def register(self, name: str, backend: CacheBackend) -> None:
        """Register a backend once under a non-empty stable name."""
        if not name:
            raise ValueError("backend name must not be empty")
        with self._lock:
            if name in self._backends:
                raise CacheError(f"Cache backend '{name}' is already registered")
            self._backends[name] = backend

    def get(self, name: str = "memory") -> CacheBackend:
        """Return a registered backend or raise a typed missing-backend error."""
        with self._lock:
            try:
                return self._backends[name]
            except KeyError as error:
                raise CacheBackendNotFoundError(
                    f"Cache backend '{name}' is not registered"
                ) from error

    def list(self) -> list[tuple[str, CacheBackend]]:
        """Return named backends in stable order."""
        with self._lock:
            return [(name, self._backends[name]) for name in sorted(self._backends)]

    def clear(self) -> None:
        """Clear every backend content without unregistering backend instances."""
        with self._lock:
            for backend in self._backends.values():
                backend.clear()
