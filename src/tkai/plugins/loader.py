"""Dynamic loading of plugin entry points."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any

from tkai.core.exceptions import PluginError

from .manifest import PluginManifest
from .models import PluginDefinition


class PluginLoader:
    """Resolve ``module:Class`` entries from a plugin directory."""

    def load(self, plugin_dir: str | Path, manifest: PluginManifest) -> Any:
        """Construct the instance declared by ``manifest``."""
        plugin_type = self.resolve(plugin_dir, manifest.entry)
        try:
            return plugin_type()
        except TypeError as exc:
            raise PluginError(f"Unable to construct plugin '{manifest.name}'") from exc

    def resolve(self, plugin_dir: str | Path, entry: str) -> type[Any]:
        """Resolve a plugin entry point to its implementation class."""
        module_name, separator, attribute = entry.partition(":")
        if not separator or not module_name or not attribute:
            raise PluginError("Plugin entry must use 'module:Class' syntax")
        if not all(part.isidentifier() for part in module_name.split(".")):
            raise PluginError(f"Invalid plugin module name: {module_name}")

        module = self._load_module(Path(plugin_dir), module_name)
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


class MarketplacePluginLoader(PluginLoader):
    """Load marketplace plugins after version and dependency validation."""

    def validate(
        self,
        definition: PluginDefinition,
        installed_versions: dict[str, str],
    ) -> None:
        if not definition.version or any(
            character.isspace() for character in definition.version
        ):
            raise PluginError(f"Invalid plugin version: {definition.version}")
        missing = [
            dependency.plugin_id
            for dependency in definition.dependencies
            if installed_versions.get(dependency.plugin_id) != dependency.version
        ]
        if missing:
            raise PluginError(f"Unsatisfied plugin dependencies: {sorted(missing)}")

    def load_definition(
        self,
        plugin_dir: str | Path,
        definition: PluginDefinition,
        installed_versions: dict[str, str],
    ) -> Any:
        self.validate(definition, installed_versions)
        plugin_type = self.resolve(plugin_dir, definition.entry)
        try:
            instance = plugin_type()
        except TypeError as exc:
            raise PluginError(
                f"Unable to construct plugin '{definition.plugin_id}'"
            ) from exc
        callback = getattr(instance, "initialize", None)
        if callable(callback):
            callback()
        return instance

    @staticmethod
    def unload(instance: Any) -> None:
        callback = getattr(instance, "shutdown", None)
        if callable(callback):
            callback()
        module_name = getattr(instance.__class__, "__module__", "")
        if module_name.startswith("_tkai_plugin_"):
            sys.modules.pop(module_name, None)
