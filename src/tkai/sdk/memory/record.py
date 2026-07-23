"""Immutable records and categories used by the Memory SDK contract."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType

from .namespace import MemoryNamespace
from .session import MemorySession


class MemoryType(str, Enum):
    """Portable memory categories; no category implies a backend implementation."""

    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    SESSION = "session"
    CONVERSATION = "conversation"
    TEMPORARY = "temporary"
    REFERENCE = "reference"
    CAPABILITY = "capability"


class MemoryKind(str, Enum):
    """Compatibility categories retained from the original SDK memory contract."""

    SHORT = "short"
    LONG = "long"
    VECTOR = "vector"
    REDIS = "redis"


@dataclass(frozen=True, slots=True)
class MemoryRecord:
    """A compatible record extended with isolated local-memory addressing fields."""

    key: str
    value: object
    kind: MemoryKind = MemoryKind.SHORT
    metadata: Mapping[str, object] = field(default_factory=dict)
    memory_type: MemoryType = MemoryType.SHORT_TERM
    namespace: MemoryNamespace = MemoryNamespace()
    session: MemorySession | None = None
    expires_at: datetime | None = None

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("Memory record key must not be empty.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
