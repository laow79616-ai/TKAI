"""Immutable local reference-memory configuration without discovery or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .errors import MemoryConfigurationError


@dataclass(frozen=True, slots=True)
class MemoryConfiguration:
    """Bounded local-memory settings explicitly supplied by the application."""

    capacity: int = 100
    default_ttl_seconds: float | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.capacity < 1:
            raise MemoryConfigurationError("Memory capacity must be at least one.")
        if self.default_ttl_seconds is not None and self.default_ttl_seconds < 0:
            raise MemoryConfigurationError("Memory TTL must be non-negative.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
