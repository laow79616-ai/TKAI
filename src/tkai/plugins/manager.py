"""Plugin discovery, lifecycle, and registration services."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, cast

from tkai.core.context import Context
from tkai.core.exceptions import PluginError

from .discovery import PluginDiscovery
from .loader import PluginLoader
from .manifest import PluginManifest
from .registry import PluginRegistry


class Plugin(Protocol):
    """The lifecycle contract implemented by loadable TKAI plugins."""

    def activate(self, context: Context) -> None:
        """Initialize plugin services in the supplied application context."""

    def deactivate(self, context: Context) -> None:
        """Release plugin services from the supplied application context."""


class PluginManager:
    """Discover and manage independently packaged TKAI plugins."""

    def __init__(self, context: Context | None = None) -> None:
        self.context = context or Context()
        self.registry = PluginRegistry()
        self.loader = PluginLoader()

    def discover(self, root: str | Path | None = None) -> list[PluginManifest]:
        """Return valid manifests found directly below a plugin root directory."""
        return PluginDiscovery(root).discover()

    def load_all(self, root: str | Path | None = None) -> list[Plugin]:
        """Discover and activate every enabled plugin below ``root``."""
        discovery = PluginDiscovery(root)
        return [
            self.load(discovery.root / manifest.name)
            for manifest in discovery.discover()
            if manifest.enabled
        ]

    def load(self, plugin_dir: str | Path) -> Plugin:
        """Load, register, and activate the plugin declared in ``plugin_dir``."""
        directory = Path(plugin_dir)
        manifest = PluginManifest.load(directory)
        if not manifest.enabled:
            raise PluginError(f"Plugin '{manifest.name}' is disabled")

        plugin = cast(Plugin, self.loader.load(directory, manifest))

        self.register(plugin, manifest)
        try:
            plugin.activate(self.context)
        except Exception:
            self.unregister(manifest.name)
            raise
        return plugin

    def register(self, plugin: Plugin, manifest: PluginManifest) -> None:
        """Register a plugin instance without activating it."""
        self._validate_plugin(plugin, manifest.name)
        self.registry.register(plugin, manifest)

    def unload(self, name: str) -> Plugin:
        """Deactivate and unregister a loaded plugin."""
        plugin = self.get(name)
        try:
            plugin.deactivate(self.context)
        finally:
            self.unregister(name)
        return plugin

    def unregister(self, name: str) -> Plugin:
        """Unregister a plugin without calling its lifecycle hooks."""
        return self.registry.unregister(name)

    def get(self, name: str) -> Plugin:
        """Return a registered plugin by name."""
        return self.registry.get(name)

    def manifest(self, name: str) -> PluginManifest:
        """Return metadata for a registered plugin."""
        return self.registry.manifest(name)

    def names(self) -> list[str]:
        """Return registered plugin names in stable order."""
        return self.registry.names()

    @staticmethod
    def _validate_plugin(plugin: Any, name: str) -> None:
        for method in ("activate", "deactivate"):
            if not callable(getattr(plugin, method, None)):
                raise PluginError(f"Plugin '{name}' does not define {method}()")
