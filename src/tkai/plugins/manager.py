"""Plugin discovery, lifecycle, and registration services."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Protocol

from tkai.core.context import Context
from tkai.core.exceptions import PluginError

from .manifest import PluginManifest


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
        self._plugins: dict[str, Plugin] = {}
        self._manifests: dict[str, PluginManifest] = {}

    def discover(self, root: str | Path) -> list[PluginManifest]:
        """Return valid manifests found directly below a plugin root directory."""
        root_path = Path(root)
        if not root_path.is_dir():
            return []

        manifests: list[PluginManifest] = []
        for directory in sorted(root_path.iterdir()):
            if not directory.is_dir() or directory.name == "__pycache__":
                continue
            try:
                manifests.append(PluginManifest.load(directory))
            except PluginError as exc:
                if (directory / "plugin.json").exists():
                    raise PluginError(
                        f"Failed to discover plugin: {directory}"
                    ) from exc
        return manifests

    def load(self, plugin_dir: str | Path) -> Plugin:
        """Load, register, and activate the plugin declared in ``plugin_dir``."""
        directory = Path(plugin_dir)
        manifest = PluginManifest.load(directory)
        if not manifest.enabled:
            raise PluginError(f"Plugin '{manifest.name}' is disabled")

        plugin_type = self._resolve_entry(directory, manifest.entry)
        try:
            plugin = plugin_type()
        except TypeError as exc:
            raise PluginError(f"Unable to construct plugin '{manifest.name}'") from exc

        self.register(plugin, manifest)
        try:
            plugin.activate(self.context)
        except Exception:
            self.unregister(manifest.name)
            raise
        return plugin

    def register(self, plugin: Plugin, manifest: PluginManifest) -> None:
        """Register a plugin instance without activating it."""
        if manifest.name in self._plugins:
            raise PluginError(f"Plugin '{manifest.name}' already registered")
        self._validate_plugin(plugin, manifest.name)
        self._plugins[manifest.name] = plugin
        self._manifests[manifest.name] = manifest

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
        if name not in self._plugins:
            raise PluginError(f"Plugin '{name}' is not registered")
        self._manifests.pop(name, None)
        return self._plugins.pop(name)

    def get(self, name: str) -> Plugin:
        """Return a registered plugin by name."""
        try:
            return self._plugins[name]
        except KeyError as exc:
            raise PluginError(f"Plugin '{name}' is not registered") from exc

    def manifest(self, name: str) -> PluginManifest:
        """Return metadata for a registered plugin."""
        try:
            return self._manifests[name]
        except KeyError as exc:
            raise PluginError(f"Plugin '{name}' is not registered") from exc

    def names(self) -> list[str]:
        """Return registered plugin names in stable order."""
        return sorted(self._plugins)

    @staticmethod
    def _validate_plugin(plugin: Any, name: str) -> None:
        for method in ("activate", "deactivate"):
            if not callable(getattr(plugin, method, None)):
                raise PluginError(f"Plugin '{name}' does not define {method}()")

    @staticmethod
    def _resolve_entry(plugin_dir: Path, entry: str) -> type[Plugin]:
        module_name, separator, attribute = entry.partition(":")
        if not separator or not module_name or not attribute:
            raise PluginError("Plugin entry must use 'module:Class' syntax")
        if not all(part.isidentifier() for part in module_name.split(".")):
            raise PluginError(f"Invalid plugin module name: {module_name}")

        module = PluginManager._load_module(plugin_dir, module_name)
        plugin_type = getattr(module, attribute, None)
        if not isinstance(plugin_type, type):
            raise PluginError(f"Plugin entry '{entry}' does not reference a class")
        return plugin_type

    @staticmethod
    def _load_module(plugin_dir: Path, module_name: str) -> ModuleType:
        relative = Path(*module_name.split("."))
        source = plugin_dir / relative.with_suffix(".py")
        if not source.is_file():
            source = plugin_dir / relative / "__init__.py"
        if not source.is_file():
            raise PluginError(f"Plugin module not found: {module_name}")

        unique_name = f"_tkai_plugin_{plugin_dir.name}_{module_name}"
        spec = importlib.util.spec_from_file_location(unique_name, source)
        if spec is None or spec.loader is None:
            raise PluginError(f"Unable to load plugin module: {module_name}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
