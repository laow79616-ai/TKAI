"""Policy protocols reserved for explicit Memory SDK customisation."""

from __future__ import annotations

from typing import Protocol

from .record import MemoryRecord


class MemoryPolicy(Protocol):
    """Base contract for opt-in policies; no policy is enabled implicitly."""

    @property
    def name(self) -> str: ...

    @property
    def enabled(self) -> bool: ...


class EvictionPolicy(MemoryPolicy, Protocol):
    """Select a record key to evict when a bounded memory reaches capacity."""

    def select(self, records: tuple[MemoryRecord, ...]) -> str | None: ...


class TTLPolicy(MemoryPolicy, Protocol):
    """Decide whether a record has expired at an application-supplied instant."""

    def expired(self, record: MemoryRecord) -> bool: ...


class CapacityPolicy(MemoryPolicy, Protocol):
    """Decide whether a proposed record fits within local capacity."""

    def allows(self, size: int) -> bool: ...


class OverwritePolicy(MemoryPolicy, Protocol):
    """Decide whether an existing record can be replaced."""

    def allows(self, existing: MemoryRecord, replacement: MemoryRecord) -> bool: ...


class SnapshotPolicy(MemoryPolicy, Protocol):
    """Transform a record before an explicit snapshot is exposed."""

    def copy(self, record: MemoryRecord) -> MemoryRecord: ...


class RetentionPolicy(MemoryPolicy, Protocol):
    """Decide whether a record remains eligible for local retention."""

    def retain(self, record: MemoryRecord) -> bool: ...
