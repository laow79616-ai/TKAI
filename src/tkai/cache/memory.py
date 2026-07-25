"""Thread-safe in-memory cache backend with TTL and shared EventBus events."""

from __future__ import annotations

import sys
from collections.abc import Callable
from datetime import datetime, timezone
from threading import RLock

from tkai.observability import EventBus

from .backend import CacheBackend
from .events import CacheEvent, CacheEvicted, CacheExpired, CacheHit, CacheMiss
from .models import CacheEntry, CacheStatistics

Clock = Callable[[], datetime]


def _utc_now() -> datetime:
    """Return the default UTC clock used for deterministic expiration checks."""
    return datetime.now(timezone.utc)


class InMemoryBackend(CacheBackend):
    """Store immutable entries locally; callers never receive mutable internal data."""

    def __init__(
        self,
        *,
        name: str = "memory",
        event_bus: EventBus | None = None,
        clock: Clock = _utc_now,
    ) -> None:
        self.name = name
        self._event_bus = event_bus
        self._clock = clock
        self._entries: dict[str, CacheEntry] = {}
        self._statistics = CacheStatistics()
        self._lock = RLock()
        self.events: list[CacheEvent] = []

    def get(self, key: str) -> CacheEntry | None:
        """Return an accessed entry, safely evicting expired values on read."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                self._statistics = CacheStatistics(
                    self._statistics.hits,
                    self._statistics.misses + 1,
                    self._statistics.expired,
                    self._statistics.evicted,
                )
                self._publish(CacheMiss(key=key, backend=self.name, data={"key": key}))
                return None
            if entry.expired(self._clock()):
                del self._entries[key]
                self._statistics = CacheStatistics(
                    self._statistics.hits,
                    self._statistics.misses + 1,
                    self._statistics.expired + 1,
                    self._statistics.evicted,
                )
                self._publish(
                    CacheExpired(key=key, backend=self.name, data={"key": key})
                )
                return None
            accessed = entry.accessed(self._clock())
            self._entries[key] = accessed
            self._statistics = CacheStatistics(
                self._statistics.hits + 1,
                self._statistics.misses,
                self._statistics.expired,
                self._statistics.evicted,
            )
            self._publish(CacheHit(key=key, backend=self.name, data={"key": key}))
            return accessed

    def set(self, entry: CacheEntry) -> None:
        """Store a caller-owned immutable entry under its stable key."""
        with self._lock:
            self._entries[entry.key] = entry

    def delete(self, key: str) -> bool:
        """Evict one entry and publish only when it actually existed."""
        with self._lock:
            if key not in self._entries:
                return False
            del self._entries[key]
            self._statistics = CacheStatistics(
                self._statistics.hits,
                self._statistics.misses,
                self._statistics.expired,
                self._statistics.evicted + 1,
            )
            self._publish(CacheEvicted(key=key, backend=self.name, data={"key": key}))
            return True

    def contains(self, key: str) -> bool:
        """Return whether a live entry exists, accounting for expiry consistently."""
        return self.get(key) is not None

    def clear(self) -> None:
        """Evict all current entries while retaining cumulative observability stats."""
        with self._lock:
            keys = tuple(self._entries)
            self._entries.clear()
            for key in keys:
                self._publish(
                    CacheEvicted(key=key, backend=self.name, data={"key": key})
                )
            self._statistics = CacheStatistics(
                self._statistics.hits,
                self._statistics.misses,
                self._statistics.expired,
                self._statistics.evicted + len(keys),
            )

    def size(self) -> int:
        """Return the live local entry count after removing expired values."""
        with self._lock:
            for key in tuple(self._entries):
                entry = self._entries[key]
                if entry.expired(self._clock()):
                    del self._entries[key]
            return len(self._entries)

    def statistics(self) -> CacheStatistics:
        """Return immutable backend statistics."""
        with self._lock:
            return self._statistics

    def estimated_memory(self) -> int:
        """Estimate top-level key and entry object sizes deterministically."""
        with self._lock:
            return sum(
                sys.getsizeof(key) + sys.getsizeof(entry)
                for key, entry in self._entries.items()
            )

    def _publish(self, event: CacheEvent) -> None:
        self.events.append(event)
        if self._event_bus is not None:
            self._event_bus.publish(event)
