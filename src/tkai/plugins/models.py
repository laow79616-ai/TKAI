"""Immutable metadata for SDK plugins while retaining legacy manifests."""

from __future__ import annotations

from dataclasses import asdict, dataclass


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
