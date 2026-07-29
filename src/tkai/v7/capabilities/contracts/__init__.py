"""Contracts for the opt-in V7 unified capability framework."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from tkai.v7.contracts import Version, VersionRange


class CapabilityStatus(str, Enum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    LOADED = "loaded"
    ACTIVE = "active"
    PAUSED = "paused"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class HealthStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class Dependency:
    capability_id: str
    versions: VersionRange = field(
        default_factory=lambda: VersionRange(Version(0), Version(999, 999, 999))
    )
    optional: bool = False


@dataclass(frozen=True)
class Interface:
    name: str
    version: Version = field(default_factory=lambda: Version(1))


@dataclass(frozen=True)
class UpgradePath:
    from_version: Version
    to_version: Version
    description: str = ""


@dataclass(frozen=True)
class Deprecation:
    deprecated_at: str
    replacement: str | None = None
    retire_at: str | None = None
    message: str = ""


@dataclass(frozen=True)
class Health:
    status: HealthStatus = HealthStatus.UNKNOWN
    ready: bool = False
    live: bool = False
    diagnostics: Mapping[str, object] = field(default_factory=dict)
    last_heartbeat: str | None = None


@dataclass(frozen=True)
class Metrics:
    load_count: int = 0
    activation_count: int = 0
    errors: int = 0
    latency_ms: float = 0.0
    availability: float = 0.0


@dataclass(frozen=True)
class CapabilityModel:
    capability_id: str
    name: str
    description: str
    owner: str
    version: Version
    category: str
    status: CapabilityStatus = CapabilityStatus.REGISTERED
    dependencies: tuple[Dependency, ...] = ()
    interfaces: tuple[Interface, ...] = ()
    permissions: frozenset[str] = frozenset()
    health: Health = Health()
    metrics: Metrics = Metrics()
    audit: tuple[Mapping[str, object], ...] = ()
    tags: frozenset[str] = frozenset()
    metadata: Mapping[str, object] = field(default_factory=dict)
    lifecycle: tuple[CapabilityStatus, ...] = (CapabilityStatus.REGISTERED,)
    configuration: Mapping[str, object] = field(default_factory=dict)
    upgrade_paths: tuple[UpgradePath, ...] = ()
    deprecation: Deprecation | None = None


@runtime_checkable
class CapabilityProvider(Protocol):
    @property
    def capability(self) -> CapabilityModel: ...

    def load(self) -> None: ...

    def activate(self) -> None: ...

    def pause(self) -> None: ...

    def disable(self) -> None: ...


def serialize(value: Any) -> Any:
    """Convert framework values to JSON-safe structures without configuration."""
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Version):
        return str(value)
    if hasattr(value, "__dataclass_fields__"):
        return {
            key: serialize(item)
            for key, item in vars(value).items()
            if key != "configuration"
        }
    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    return value


__all__ = (
    "CapabilityModel",
    "CapabilityProvider",
    "CapabilityStatus",
    "Dependency",
    "Deprecation",
    "Health",
    "HealthStatus",
    "Interface",
    "Metrics",
    "UpgradePath",
    "serialize",
)
