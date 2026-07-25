"""Thread-safe explicit registry for Memory SDK implementations."""

from __future__ import annotations

from threading import RLock

from .base import Memory
from .errors import MemoryNotFoundError


class MemoryRegistry:
    """Store explicitly registered memories without creating a default backend."""

    def __init__(self) -> None:
        self._memories: dict[str, Memory] = {}
        self._lock = RLock()

    def register(self, memory: Memory) -> Memory:
        """Register one uniquely named memory implementation."""
        with self._lock:
            if memory.name in self._memories:
                raise ValueError(f"Memory already registered: {memory.name}")
            self._memories[memory.name] = memory
        return memory

    def unregister(self, name: str) -> Memory:
        """Remove one memory without closing it implicitly."""
        with self._lock:
            try:
                return self._memories.pop(name)
            except KeyError as error:
                raise MemoryNotFoundError(f"Memory not registered: {name}") from error

    def lookup(self, name: str) -> Memory:
        """Return a registered memory or a clear SDK error."""
        with self._lock:
            try:
                return self._memories[name]
            except KeyError as error:
                raise MemoryNotFoundError(f"Memory not registered: {name}") from error

    def list(self) -> tuple[Memory, ...]:
        """Return stable name-sorted registered memory implementations."""
        with self._lock:
            return tuple(self._memories[name] for name in sorted(self._memories))
