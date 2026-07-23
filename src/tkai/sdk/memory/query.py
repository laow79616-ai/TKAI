"""Memory query and result value objects with deterministic result ordering."""

from __future__ import annotations

from dataclasses import dataclass

from .namespace import MemoryNamespace
from .record import MemoryRecord, MemoryType
from .session import MemorySession


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    """Local exact-filter query; it deliberately performs no semantic search."""

    namespace: MemoryNamespace | None = None
    session: MemorySession | None = None
    memory_type: MemoryType | None = None
    key_prefix: str = ""


@dataclass(frozen=True, slots=True)
class MemoryResult:
    """Stable, immutable collection returned by list and query operations."""

    records: tuple[MemoryRecord, ...] = ()
