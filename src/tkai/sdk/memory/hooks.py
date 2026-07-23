"""Optional observer contracts for explicit Memory SDK integrations."""

from __future__ import annotations

from typing import Protocol

from .query import MemoryQuery, MemoryResult
from .record import MemoryRecord


class MemoryHook(Protocol):
    """Non-owning observer contract for explicit memory operations."""

    def before_store(self, record: MemoryRecord) -> None: ...

    def after_store(self, record: MemoryRecord) -> None: ...

    def before_query(self, query: MemoryQuery) -> None: ...

    def after_query(self, result: MemoryResult) -> None: ...

    def on_error(self, error: Exception) -> None: ...


class TelemetryMemoryHook(MemoryHook, Protocol):
    """Marker contract for a caller-supplied telemetry observer."""
