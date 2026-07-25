"""Thread-safe local reference memory and composition-only memory adapter."""

from __future__ import annotations

from collections import OrderedDict
from threading import RLock

from ..errors import SDKMemoryError
from ..memory import Memory, MemoryRecord


class InMemoryMemory:
    """Bounded, namespace-aware reference memory for tests and examples only."""

    def __init__(self, *, capacity: int = 100, namespace: str = "default") -> None:
        if capacity < 1 or not namespace:
            raise SDKMemoryError(
                "Memory capacity must be positive and namespace non-empty."
            )
        self.capacity = capacity
        self.namespace = namespace
        self._records: OrderedDict[str, MemoryRecord] = OrderedDict()
        self._lock = RLock()

    def put(self, record: MemoryRecord) -> None:
        """Store or replace a record, evicting the least-recently inserted record."""
        if not record.key:
            raise SDKMemoryError("Memory record key must not be empty.")
        stored = MemoryRecord(
            record.key, record.value, record.kind, dict(record.metadata)
        )
        with self._lock:
            self._records.pop(record.key, None)
            self._records[record.key] = stored
            while len(self._records) > self.capacity:
                self._records.popitem(last=False)

    store = put

    def get(self, key: str) -> MemoryRecord | None:
        """Return a defensive immutable record copy for one key."""
        with self._lock:
            record = self._records.get(key)
        return self._copy(record) if record is not None else None

    def delete(self, key: str) -> bool:
        """Delete one record and report whether it existed."""
        with self._lock:
            return self._records.pop(key, None) is not None

    def list(self) -> tuple[MemoryRecord, ...]:
        """Return stable defensive copies in insertion order."""
        with self._lock:
            return tuple(self._copy(record) for record in self._records.values())

    def query(self, prefix: str = "") -> tuple[MemoryRecord, ...]:
        """Return local key-prefix matches; this is not semantic or vector search."""
        return tuple(record for record in self.list() if record.key.startswith(prefix))

    def clear(self) -> None:
        """Remove all records without starting background cleanup work."""
        with self._lock:
            self._records.clear()

    @staticmethod
    def _copy(record: MemoryRecord) -> MemoryRecord:
        return MemoryRecord(
            record.key, record.value, record.kind, dict(record.metadata)
        )


class MemoryAdapter:
    """Compose any SDK Memory implementation without changing its lifecycle."""

    def __init__(self, memory: Memory) -> None:
        self.memory = memory

    def context(self, key: str) -> object | None:
        """Read one value for explicit request-context injection."""
        record = self.memory.get(key)
        return record.value if record is not None else None
