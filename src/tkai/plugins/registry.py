"""In-memory registry for plugin instances and metadata."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, Any

from tkai.core.exceptions import PluginError

from .manifest import PluginManifest
from .models import InstalledPlugin, PluginDefinition, PluginMetadata, PluginState

if TYPE_CHECKING:
    from .manager import Plugin


class PluginRegistry:
    """Store registered plugins while enforcing unique manifest names."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._manifests: dict[str, PluginManifest] = {}
        self._metadata: dict[str, PluginMetadata] = {}
        self._enabled: set[str] = set()
        self._lock = RLock()

    def register(self, plugin: Plugin, manifest: PluginManifest) -> None:
        """Register one plugin and its manifest."""
        self.register_sdk(
            plugin,
            PluginMetadata(
                manifest.name,
                manifest.version,
                manifest.description,
                enabled=manifest.enabled,
            ),
            manifest,
        )

    def register_sdk(
        self,
        plugin: Any,
        metadata: PluginMetadata,
        manifest: PluginManifest | None = None,
    ) -> None:
        """Register SDK metadata while retaining optional legacy manifest access."""
        with self._lock:
            if metadata.name in self._plugins:
                raise PluginError(f"Plugin '{metadata.name}' already registered")
            self._plugins[metadata.name] = plugin
            self._metadata[metadata.name] = metadata
            if manifest is not None:
                self._manifests[metadata.name] = manifest
            if metadata.enabled:
                self._enabled.add(metadata.name)

    def unregister(self, name: str) -> Plugin:
        """Remove and return a registered plugin."""
        with self._lock:
            if name not in self._plugins:
                raise PluginError(f"Plugin '{name}' is not registered")
            self._manifests.pop(name, None)
            self._metadata.pop(name, None)
            self._enabled.discard(name)
            return self._plugins.pop(name)

    def get(self, name: str) -> Plugin:
        """Return a plugin by name."""
        with self._lock:
            try:
                return self._plugins[name]
            except KeyError as exc:
                raise PluginError(f"Plugin '{name}' is not registered") from exc

    def metadata(self, name: str) -> PluginMetadata:
        """Return SDK metadata for a registered plugin."""
        with self._lock:
            try:
                return self._metadata[name]
            except KeyError as exc:
                raise PluginError(f"Plugin '{name}' is not registered") from exc

    def enable(self, name: str) -> None:
        self.get(name)
        with self._lock:
            self._enabled.add(name)

    def disable(self, name: str) -> None:
        self.get(name)
        with self._lock:
            self._enabled.discard(name)

    def enabled(self, name: str) -> bool:
        self.get(name)
        with self._lock:
            return name in self._enabled

    def clear(self) -> None:
        with self._lock:
            self._plugins.clear()
            self._manifests.clear()
            self._metadata.clear()
            self._enabled.clear()

    def manifest(self, name: str) -> PluginManifest:
        """Return the manifest for a registered plugin."""
        with self._lock:
            try:
                return self._manifests[name]
            except KeyError as exc:
                raise PluginError(f"Plugin '{name}' is not registered") from exc

    def names(self) -> list[str]:
        """Return registered plugin names in stable order."""
        with self._lock:
            return sorted(self._plugins)


class MarketplaceRegistry:
    """Thread-safe installed-plugin registry with upgrade history and rollback."""

    def __init__(self) -> None:
        self._installed: dict[str, InstalledPlugin] = {}
        self._lock = RLock()

    def install(
        self, definition: PluginDefinition, installed_at: float
    ) -> InstalledPlugin:
        with self._lock:
            if definition.plugin_id in self._installed:
                raise PluginError(f"Plugin '{definition.plugin_id}' is installed")
            record = InstalledPlugin(definition, PluginState.INSTALLED, installed_at)
            self._installed[definition.plugin_id] = record
            return record

    def uninstall(self, plugin_id: str) -> InstalledPlugin:
        with self._lock:
            try:
                return self._installed.pop(plugin_id)
            except KeyError as exc:
                raise PluginError(f"Plugin '{plugin_id}' is not installed") from exc

    def get(self, plugin_id: str) -> InstalledPlugin:
        with self._lock:
            try:
                return self._installed[plugin_id]
            except KeyError as exc:
                raise PluginError(f"Plugin '{plugin_id}' is not installed") from exc

    def set_state(self, plugin_id: str, state: PluginState) -> InstalledPlugin:
        with self._lock:
            current = self.get(plugin_id)
            updated = InstalledPlugin(
                current.definition,
                state,
                current.installed_at,
                current.previous_versions,
            )
            self._installed[plugin_id] = updated
            return updated

    def upgrade(
        self, plugin_id: str, definition: PluginDefinition, installed_at: float
    ) -> InstalledPlugin:
        with self._lock:
            current = self.get(plugin_id)
            if current.definition.plugin_id != definition.plugin_id:
                raise PluginError("Upgrade plugin id does not match installed plugin")
            updated = InstalledPlugin(
                definition,
                current.state,
                installed_at,
                current.previous_versions + (current.definition,),
            )
            self._installed[plugin_id] = updated
            return updated

    def rollback(self, plugin_id: str, installed_at: float) -> InstalledPlugin:
        with self._lock:
            current = self.get(plugin_id)
            if not current.previous_versions:
                raise PluginError(f"Plugin '{plugin_id}' has no rollback version")
            previous = current.previous_versions[-1]
            updated = InstalledPlugin(
                previous,
                current.state,
                installed_at,
                current.previous_versions[:-1],
            )
            self._installed[plugin_id] = updated
            return updated

    def list(self) -> tuple[InstalledPlugin, ...]:
        with self._lock:
            return tuple(self._installed[key] for key in sorted(self._installed))

    def search(self, query: str) -> tuple[InstalledPlugin, ...]:
        needle = query.casefold()
        return tuple(
            item
            for item in self.list()
            if needle in item.definition.plugin_id.casefold()
            or needle in item.definition.name.casefold()
            or needle in item.definition.description.casefold()
        )
