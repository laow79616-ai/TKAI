"""Thread-safe registry for explicitly selected adaptive routers."""

from __future__ import annotations

from threading import RLock

from .errors import AdaptiveRouterNotFoundError, AdaptiveRoutingError


class AdaptiveRouterRegistry:
    """Own named routers and enabled state with stable list order."""

    def __init__(self) -> None:
        self._routers: dict[str, object] = {}
        self._enabled: set[str] = set()
        self._lock = RLock()

    def register(self, name: str, router: object, *, enabled: bool = True) -> None:
        if not name:
            raise AdaptiveRoutingError("router name must not be empty")
        with self._lock:
            if name in self._routers:
                raise AdaptiveRoutingError(f"Adaptive router '{name}' is registered")
            self._routers[name] = router
            if enabled:
                self._enabled.add(name)

    def unregister(self, name: str) -> object:
        with self._lock:
            try:
                self._enabled.discard(name)
                return self._routers.pop(name)
            except KeyError as error:
                raise AdaptiveRouterNotFoundError(
                    f"Adaptive router '{name}' is not registered"
                ) from error

    def get(self, name: str) -> object:
        with self._lock:
            try:
                return self._routers[name]
            except KeyError as error:
                raise AdaptiveRouterNotFoundError(
                    f"Adaptive router '{name}' is not registered"
                ) from error

    def list(self) -> list[tuple[str, object]]:
        with self._lock:
            return [(name, self._routers[name]) for name in sorted(self._routers)]

    def enable(self, name: str) -> None:
        self.get(name)
        with self._lock:
            self._enabled.add(name)

    def disable(self, name: str) -> None:
        self.get(name)
        with self._lock:
            self._enabled.discard(name)

    def enabled(self, name: str) -> bool:
        self.get(name)
        with self._lock:
            return name in self._enabled

    def clear(self) -> None:
        with self._lock:
            self._routers.clear()
            self._enabled.clear()
