"""Plugin discovery, lifecycle, and registration services."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol, cast

from tkai.core.context import Context
from tkai.core.exceptions import PluginError
from tkai.observability import EventBus

from .discovery import PluginDiscovery
from .events import (
    PluginDisabled,
    PluginEnabled,
    PluginEvent,
    PluginFailed,
    PluginLoaded,
    PluginUnloaded,
)
from .hooks import Hook
from .lifecycle import initialize_plugin, shutdown_plugin
from .loader import PluginLoader
from .manifest import PluginManifest
from .models import PluginMetadata
from .registry import PluginRegistry


class Plugin(Protocol):
    """The lifecycle contract implemented by loadable TKAI plugins."""

    def activate(self, context: Context) -> None:
        """Initialize plugin services in the supplied application context."""

    def deactivate(self, context: Context) -> None:
        """Release plugin services from the supplied application context."""


class PluginManager:
    """Discover and manage independently packaged TKAI plugins."""

    def __init__(
        self, context: Context | None = None, *, event_bus: EventBus | None = None
    ) -> None:
        self.context = context or Context()
        self.registry = PluginRegistry()
        self.loader = PluginLoader()
        self.event_bus = event_bus
        self.events: list[PluginEvent] = []

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

    def register_sdk(self, plugin: Any, metadata: PluginMetadata) -> None:
        """Register and initialize a local SDK plugin with failure isolation."""
        self.registry.register_sdk(plugin, metadata)
        try:
            initialize_plugin(plugin, self.context)
        except Exception:
            self.registry.unregister(metadata.name)
            self._publish(PluginFailed(plugin=metadata.name, version=metadata.version))
            raise
        self._publish(PluginLoaded(plugin=metadata.name, version=metadata.version))

    def enable(self, name: str) -> None:
        """Enable a registered plugin and invoke its optional enable callback."""
        plugin = self.get(name)
        callback = getattr(plugin, "on_enable", None)
        if callable(callback):
            callback()
        self.registry.enable(name)
        metadata = self.registry.metadata(name)
        self._publish(PluginEnabled(plugin=name, version=metadata.version))

    def disable(self, name: str) -> None:
        """Disable a plugin without unloading its local Python module."""
        plugin = self.get(name)
        callback = getattr(plugin, "on_disable", None)
        if callable(callback):
            callback()
        self.registry.disable(name)
        metadata = self.registry.metadata(name)
        self._publish(PluginDisabled(plugin=name, version=metadata.version))

    def dispatch(self, hook: Hook, payload: dict[str, Any]) -> None:
        """Dispatch stable priority/name hook order while isolating plugin failures."""
        names = sorted(
            self.names(),
            key=lambda name: (-self.registry.metadata(name).priority, name),
        )
        for name in names:
            if not self.registry.enabled(name):
                continue
            handler = getattr(self.get(name), "on_hook", None)
            if not callable(handler):
                continue
            try:
                handler(hook, dict(payload))
            except Exception:
                metadata = self.registry.metadata(name)
                self._publish(PluginFailed(plugin=name, version=metadata.version))

    def unload(self, name: str) -> Plugin:
        """Deactivate and unregister a loaded plugin."""
        plugin = self.get(name)
        try:
            plugin.deactivate(self.context)
        finally:
            self.unregister(name)
        return plugin

    def unload_sdk(self, name: str) -> Any:
        """Shutdown and unregister an SDK plugin while preserving failure isolation."""
        plugin = self.get(name)
        metadata = self.registry.metadata(name)
        try:
            shutdown_plugin(plugin, self.context)
        finally:
            self.unregister(name)
        self._publish(PluginUnloaded(plugin=name, version=metadata.version))
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

    def _publish(self, event: PluginEvent) -> None:
        self.events.append(event)
        if self.event_bus is not None:
            self.event_bus.publish(event)

    @staticmethod
    def _validate_plugin(plugin: Any, name: str) -> None:
        for method in ("activate", "deactivate"):
            if not callable(getattr(plugin, method, None)):
                raise PluginError(f"Plugin '{name}' does not define {method}()")
