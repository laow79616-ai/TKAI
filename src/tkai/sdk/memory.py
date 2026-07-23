"""Memory SDK contracts for short, long, vector, and Redis adapters."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class MemoryKind(str, Enum):
    """Portable memory categories; implementations remain caller-selected."""

    SHORT = "short"
    LONG = "long"
    VECTOR = "vector"
    REDIS = "redis"


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """Immutable memory value with a stable application-owned key."""

    key: str
    value: object
    kind: MemoryKind = MemoryKind.SHORT


class Memory(Protocol):
    """Minimal storage contract with no default backend or persistence policy."""

    def get(self, key: str) -> MemoryRecord | None: ...
    def put(self, record: MemoryRecord) -> None: ...
    def clear(self) -> None: ...
