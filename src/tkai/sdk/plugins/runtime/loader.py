"""Explicit object loader for local plugin instances; no module discovery occurs."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .registry import PluginRegistry

if TYPE_CHECKING:
    from .runtime import Plugin


class PluginLoader:
    """Add supplied plugin objects to a registry without dynamic imports."""

    def __init__(self, registry: PluginRegistry) -> None:
        self.registry = registry

    def load(self, plugin: Plugin) -> Plugin:
        """Load an already constructed local plugin into the explicit registry."""
        return self.registry.register(plugin)

    def unload(self, name: str) -> Plugin:
        """Unload one plugin from the explicit registry only."""
        return self.registry.unregister(name)
