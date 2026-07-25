"""Immutable local Plugin Runtime manifests without remote discovery metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from .dependency import PluginDependency


@dataclass(frozen=True, slots=True)
class PluginManifest:
    """Describes one explicit local plugin and its declared dependencies."""

    name: str
    version: str = "0.0.0"
    author: str = ""
    description: str = ""
    dependencies: tuple[PluginDependency, ...] = ()
    capabilities: frozenset[str] = frozenset()
    entry_point: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Plugin manifest name must not be empty.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
