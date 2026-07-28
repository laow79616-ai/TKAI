"""Bounded read/write-through least-recently-used cache."""

from __future__ import annotations

from collections import OrderedDict

from ..metrics import MemoryMetrics
from ..models import MemoryObject


class MemoryCache:
    def __init__(self, metrics: MemoryMetrics, limit: int = 1000) -> None:
        if limit < 1:
            raise ValueError("Cache limit must be positive.")
        self.metrics = metrics
        self.limit = limit
        self._items: OrderedDict[str, MemoryObject] = OrderedDict()
        self.evictions = 0

    def read(self, memory_id: str) -> MemoryObject | None:
        item = self._items.get(memory_id)
        metric = (
            "memory_cache_hits_total"
            if item is not None
            else "memory_cache_misses_total"
        )
        self.metrics.increment(metric)
        if item is not None:
            self._items.move_to_end(memory_id)
        return item

    def write(self, memory: MemoryObject) -> None:
        self._items[memory.id] = memory
        self._items.move_to_end(memory.id)
        while len(self._items) > self.limit:
            self._items.popitem(last=False)
            self.evictions += 1

    def evict(self, memory_id: str) -> None:
        self._items.pop(memory_id, None)

    def clear(self) -> None:
        self._items.clear()

    def snapshot(self) -> dict[str, int]:
        return {
            "size": len(self._items),
            "limit": self.limit,
            "evictions": self.evictions,
        }
