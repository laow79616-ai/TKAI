"""In-memory registry for plugin instances and metadata."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tkai.core.exceptions import PluginError

from .manifest import PluginManifest

if TYPE_CHECKING:
    from .manager import Plugin


class PluginRegistry:
    """Store registered plugins while enforcing unique manifest names."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._manifests: dict[str, PluginManifest] = {}

    def register(self, plugin: Plugin, manifest: PluginManifest) -> None:
        """Register one plugin and its manifest."""
        if manifest.name in self._plugins:
            raise PluginError(f"Plugin '{manifest.name}' already registered")
        self._plugins[manifest.name] = plugin
        self._manifests[manifest.name] = manifest

    def unregister(self, name: str) -> Plugin:
        """Remove and return a registered plugin."""
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' is not registered")
        self._manifests.pop(name, None)
        return self._plugins.pop(name)

    def get(self, name: str) -> Plugin:
        """Return a plugin by name."""
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise PluginError(f"Plugin '{name}' is not registered") from exc

    def manifest(self, name: str) -> PluginManifest:
        """Return the manifest for a registered plugin."""
        try:
            return self._manifests[name]
        except KeyError as exc:
            raise PluginError(f"Plugin '{name}' is not registered") from exc

    def names(self) -> list[str]:
        """Return registered plugin names in stable order."""
        return sorted(self._plugins)
