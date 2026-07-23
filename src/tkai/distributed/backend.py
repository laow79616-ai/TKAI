"""Extensible synchronous and asynchronous backend contract with LocalBackend."""

from __future__ import annotations

from collections.abc import Callable
from threading import RLock
from typing import Any, Protocol


class DistributedBackend(Protocol):
    """Backend contract; implementations remain explicit and caller-owned."""

    def connect(self) -> None: ...
    def disconnect(self) -> None: ...
    def get(self, key: str) -> Any | None: ...
    def set(self, key: str, value: Any) -> None: ...
    def delete(self, key: str) -> bool: ...
    def publish(self, topic: str, value: Any) -> None: ...
    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None: ...
    def acquire_lock(self, name: str, owner: str) -> bool: ...
    def release_lock(self, name: str, owner: str) -> bool: ...
    def health(self) -> bool: ...
    async def aconnect(self) -> None: ...
    async def adisconnect(self) -> None: ...
    async def aget(self, key: str) -> Any | None: ...
    async def aset(self, key: str, value: Any) -> None: ...
    async def adelete(self, key: str) -> bool: ...


class LocalBackend:
    """Thread-safe in-memory backend used by default without network activity."""

    def __init__(self) -> None:
        self._connected = False
        self._values: dict[str, Any] = {}
        self._subscribers: dict[str, list[Callable[[Any], None]]] = {}
        self._locks: dict[str, str] = {}
        self._lock = RLock()

    def connect(self) -> None:
        """Mark the in-memory backend available; operation is idempotent."""
        with self._lock:
            self._connected = True

    def disconnect(self) -> None:
        """Mark the backend disconnected without discarding caller-owned state."""
        with self._lock:
            self._connected = False

    def get(self, key: str) -> Any | None:
        """Return a local value without exposing backend internals."""
        with self._lock:
            return self._values.get(key)

    def set(self, key: str, value: Any) -> None:
        """Store a local value for explicit coordinator use."""
        with self._lock:
            self._values[key] = value

    def delete(self, key: str) -> bool:
        """Delete a value and report whether it existed."""
        with self._lock:
            return self._values.pop(key, None) is not None

    def publish(self, topic: str, value: Any) -> None:
        """Synchronously notify a stable handler snapshot outside lock ownership."""
        with self._lock:
            handlers = tuple(self._subscribers.get(topic, ()))
        for handler in handlers:
            try:
                handler(value)
            except Exception:
                continue

    def subscribe(self, topic: str, handler: Callable[[Any], None]) -> None:
        """Register one handler once for a local topic."""
        with self._lock:
            handlers = self._subscribers.setdefault(topic, [])
            if handler not in handlers:
                handlers.append(handler)

    def acquire_lock(self, name: str, owner: str) -> bool:
        """Acquire a local named lock when unowned or owned by the same caller."""
        with self._lock:
            current = self._locks.get(name)
            if current is not None and current != owner:
                return False
            self._locks[name] = owner
            return True

    def release_lock(self, name: str, owner: str) -> bool:
        """Release a named lock only for its recorded owner."""
        with self._lock:
            if self._locks.get(name) != owner:
                return False
            del self._locks[name]
            return True

    def health(self) -> bool:
        """Return local connection state without a network probe."""
        with self._lock:
            return self._connected

    async def aconnect(self) -> None:
        self.connect()

    async def adisconnect(self) -> None:
        self.disconnect()

    async def aget(self, key: str) -> Any | None:
        return self.get(key)

    async def aset(self, key: str, value: Any) -> None:
        self.set(key, value)

    async def adelete(self, key: str) -> bool:
        return self.delete(key)


# Keep the original LocalBackend import path and name stable while making the
# default implementation explicit in backend-factory documentation.
LocalMemoryBackend = LocalBackend
