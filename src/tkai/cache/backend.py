"""Protocol-like abstract backend interface for cache implementations."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .models import CacheEntry, CacheStatistics


class CacheBackend(ABC):
    """Provide thread-safe cache storage without prescribing implementation details."""

    @abstractmethod
    def get(self, key: str) -> CacheEntry | None:
        """Return a live entry or ``None`` for miss or expiration."""

    @abstractmethod
    def set(self, entry: CacheEntry) -> None:
        """Store an immutable entry."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete one entry and return whether it was present."""

    @abstractmethod
    def contains(self, key: str) -> bool:
        """Return whether a live entry is present."""

    @abstractmethod
    def clear(self) -> None:
        """Remove every entry."""

    @abstractmethod
    def size(self) -> int:
        """Return the live entry count."""

    @abstractmethod
    def statistics(self) -> CacheStatistics:
        """Return immutable local hit/miss/eviction counters."""

    @abstractmethod
    def estimated_memory(self) -> int:
        """Return a deterministic approximate in-memory byte estimate."""
