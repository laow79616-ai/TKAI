"""Stable contracts for the internal V7 unified service mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol, runtime_checkable

from tkai.v7.contracts import Version, VersionRange


class ServiceStatus(str, Enum):
    REGISTERED = "registered"
    VALIDATED = "validated"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    DEPRECATED = "deprecated"
    RETIRED = "retired"


class HealthStatus(str, Enum):
    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass(frozen=True)
class ServiceDependency:
    service_id: str
    versions: VersionRange = field(
        default_factory=lambda: VersionRange(Version(0), Version(999, 999, 999))
    )
    interface: str | None = None
    optional: bool = False


@dataclass(frozen=True)
class ServiceInterface:
    name: str
    version: Version = field(default_factory=lambda: Version(1))


@dataclass(frozen=True)
class ServiceEndpoint:
    name: str
    reference: str
    priority: int = 100
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class ServiceHealth:
    status: HealthStatus = HealthStatus.UNKNOWN
    live: bool = False
    ready: bool = False
    available: bool = False
    diagnostics: Mapping[str, object] = field(default_factory=dict)
    last_heartbeat: str | None = None


@dataclass(frozen=True)
class ServiceMetrics:
    requests: int = 0
    successes: int = 0
    failures: int = 0
    latency_ms: float = 0.0
    availability: float = 0.0
    route_count: int = 0


@dataclass(frozen=True)
class ServiceModel:
    service_id: str
    name: str
    description: str
    version: Version
    owner: str
    category: str
    dependencies: tuple[ServiceDependency, ...] = ()
    interfaces: tuple[ServiceInterface, ...] = ()
    endpoints: tuple[ServiceEndpoint, ...] = ()
    health: ServiceHealth = ServiceHealth()
    metrics: ServiceMetrics = ServiceMetrics()
    audit: tuple[Mapping[str, object], ...] = ()
    lifecycle: tuple[ServiceStatus, ...] = (ServiceStatus.REGISTERED,)
    status: ServiceStatus = ServiceStatus.REGISTERED
    metadata: Mapping[str, object] = field(default_factory=dict)
    required_capabilities: frozenset[str] = frozenset()


@runtime_checkable
class ServiceProvider(Protocol):
    @property
    def service(self) -> ServiceModel: ...

    def start(self) -> None: ...

    def pause(self) -> None: ...

    def stop(self) -> None: ...


def serialize(value: Any) -> Any:
    """Convert mesh contracts to JSON-safe, secret-filtered structures."""
    from tkai.v7.security import filter_secrets

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Version):
        return str(value)
    if hasattr(value, "__dataclass_fields__"):
        return filter_secrets(
            {key: serialize(item) for key, item in vars(value).items()}
        )
    if isinstance(value, Mapping):
        return filter_secrets(
            {str(key): serialize(item) for key, item in value.items()}
        )
    if isinstance(value, (tuple, list, set, frozenset)):
        return [serialize(item) for item in value]
    return value


__all__ = (
    "HealthStatus",
    "ServiceDependency",
    "ServiceEndpoint",
    "ServiceHealth",
    "ServiceInterface",
    "ServiceMetrics",
    "ServiceModel",
    "ServiceProvider",
    "ServiceStatus",
    "serialize",
)
