"""Immutable metadata for SDK plugins while retaining legacy manifests."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from enum import Enum
from types import MappingProxyType


class PluginState(str, Enum):
    AVAILABLE = "available"
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"


@dataclass(frozen=True, slots=True, order=True)
class PluginDependency:
    plugin_id: str
    version: str

    def __post_init__(self) -> None:
        if not self.plugin_id or not self.version:
            raise ValueError("dependency id and version must not be empty")


@dataclass(frozen=True, slots=True)
class PluginDefinition:
    """Signed marketplace manifest and its declared runtime capabilities."""

    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    homepage: str
    license: str
    dependencies: tuple[PluginDependency, ...] = ()
    permissions: frozenset[str] = frozenset()
    tools: tuple[str, ...] = ()
    metadata: Mapping[str, str] = field(default_factory=dict)
    checksum: str = ""
    signature: str = ""
    entry: str = "plugin:Plugin"
    category: str = "other"
    tags: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        required = (
            self.plugin_id,
            self.name,
            self.version,
            self.author,
            self.description,
            self.license,
        )
        if any(not value.strip() for value in required):
            raise ValueError("plugin identity fields must not be empty")
        if any(not tool.strip() for tool in self.tools):
            raise ValueError("plugin tools must not be empty")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.plugin_id,
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "homepage": self.homepage,
            "license": self.license,
            "dependencies": [
                {"id": item.plugin_id, "version": item.version}
                for item in self.dependencies
            ],
            "permissions": sorted(self.permissions),
            "tools": list(self.tools),
            "metadata": dict(self.metadata),
            "checksum": self.checksum,
            "signature": self.signature,
            "entry": self.entry,
            "category": self.category,
            "tags": sorted(self.tags),
        }


@dataclass(frozen=True, slots=True)
class InstalledPlugin:
    definition: PluginDefinition
    state: PluginState
    installed_at: float
    previous_versions: tuple[PluginDefinition, ...] = ()

    def to_dict(self) -> dict[str, object]:
        data = self.definition.to_dict()
        data["state"] = self.state.value
        data["installed_at"] = self.installed_at
        data["previous_versions"] = [item.version for item in self.previous_versions]
        return data


@dataclass(frozen=True, slots=True)
class PluginMetadata:
    """Typed, JSON-ready plugin descriptor independent of loading source."""

    name: str
    version: str
    description: str = ""
    author: str = ""
    capabilities: frozenset[str] = frozenset()
    api_version: str = "v1"
    enabled: bool = True
    priority: int = 0

    def __post_init__(self) -> None:
        if not self.name or not self.version or not self.api_version:
            raise ValueError("plugin name, version, and api_version must not be empty")

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-ready plugin descriptor."""
        data = asdict(self)
        data["capabilities"] = sorted(self.capabilities)
        return data
