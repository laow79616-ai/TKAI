"""Immutable Tool descriptors for registration and documentation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .schema import ToolSchema


@dataclass(frozen=True, slots=True)
class ToolDescriptor:
    """Stable metadata for one explicitly registered SDK tool."""

    name: str
    description: str = ""
    schema: ToolSchema = ToolSchema()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Tool name must not be empty.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
