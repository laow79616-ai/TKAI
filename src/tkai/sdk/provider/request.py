"""Immutable transport-neutral provider request model."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType


@dataclass(frozen=True, slots=True)
class ProviderRequest:
    """One provider operation request with caller-owned, immutable metadata."""

    input: object
    model: str | None = None
    operation: str = "chat"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
