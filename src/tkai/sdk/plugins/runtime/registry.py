"""Thread-safe registry and reference dependency resolution for local plugins."""

from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING

from .dependency import resolve_dependencies
from .errors import PluginNotFoundError

if TYPE_CHECKING:
    from .runtime import Plugin


class PluginRegistry:
    """Register explicit local plugins without filesystem or remote loading."""

    def __init__(self) -> None:
        self._plugins: dict[str, Plugin] = {}
        self._lock = RLock()

    def register(self, plugin: Plugin) -> Plugin:
        """Register a uniquely named plugin and preserve the original object."""
        with self._lock:
            if plugin.manifest.name in self._plugins:
                raise ValueError(f"Plugin already registered: {plugin.manifest.name}")
            self._plugins[plugin.manifest.name] = plugin
        return plugin

    def unregister(self, name: str) -> Plugin:
        """Remove one plugin without executing or shutting it down implicitly."""
        with self._lock:
            try:
                return self._plugins.pop(name)
            except KeyError as error:
                raise PluginNotFoundError(f"Plugin not registered: {name}") from error

    def lookup(self, name: str) -> Plugin:
        """Return one registered plugin or a clear typed error."""
        with self._lock:
            try:
                return self._plugins[name]
            except KeyError as error:
                raise PluginNotFoundError(f"Plugin not registered: {name}") from error

    def list(self) -> tuple[Plugin, ...]:
        """Return a stable name-sorted registry snapshot."""
        with self._lock:
            return tuple(self._plugins[name] for name in sorted(self._plugins))

    def resolve(self, name: str) -> tuple[Plugin, ...]:
        """Return dependency-first plugins or report missing/cyclic dependencies."""
        with self._lock:
            dependencies = {
                item.manifest.name: item.manifest.dependencies
                for item in self._plugins.values()
            }
            names = resolve_dependencies(name, dependencies)
            return tuple(self._plugins[item] for item in names)
