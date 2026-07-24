"""Immutable, JSON-safe descriptors for the Marketplace Server architecture."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def _metadata(value: Mapping[str, object]) -> Mapping[str, object]:
    """Return a defensive read-only copy without reading external configuration."""
    return MappingProxyType(dict(value))


class ServerStatus(str, Enum):
    """Descriptive server states; no process lifecycle is controlled."""

    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class ServerVersion:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Server version must not be empty.")


@dataclass(frozen=True, slots=True)
class ServerCapability:
    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Server capability name must not be empty.")


@dataclass(frozen=True, slots=True)
class ServerMetadata:
    values: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _metadata(self.values))


@dataclass(frozen=True, slots=True)
class ServerConfig:
    name: str = "tkai-marketplace-server"
    version: ServerVersion = field(default_factory=lambda: ServerVersion("6.0"))
    metadata: ServerMetadata = field(default_factory=ServerMetadata)


@dataclass(frozen=True, slots=True)
class ServerInfo:
    name: str
    version: ServerVersion
    status: ServerStatus
    capabilities: tuple[ServerCapability, ...] = ()
    metadata: ServerMetadata = field(default_factory=ServerMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "capabilities",
            tuple(sorted(self.capabilities, key=lambda item: item.name)),
        )


@dataclass(frozen=True, slots=True)
class ServerStatistics:
    registries: int = 0
    publishers: int = 0
    packages: int = 0
    versions: int = 0
    releases: int = 0
    search_documents: int = 0


@dataclass(frozen=True, slots=True)
class ServerSnapshot:
    info: ServerInfo
    statistics: ServerStatistics = field(default_factory=ServerStatistics)
    closed: bool = False
