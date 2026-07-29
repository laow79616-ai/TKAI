"""Stable, execution-independent contracts for the TKAI V8 Hyper Kernel."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


class FrameworkKind(str, Enum):
    """Framework families understood by the Hyper Kernel."""

    FOUNDATION = "foundation"
    CAPABILITY = "capability"
    SERVICE_MESH = "service_mesh"
    EVENT_FABRIC = "event_fabric"
    STATE = "state"
    WORKFLOW = "workflow"
    RESOURCE = "resource"
    SECURITY = "security"
    OBSERVABILITY = "observability"
    CONFIGURATION = "configuration"
    EXTENSION = "extension"
    AI = "ai"
    DATA = "data"
    INTELLIGENCE = "intelligence"
    RUNTIME_GOVERNANCE = "runtime_governance"
    FUTURE = "future"


class HealthStatus(str, Enum):
    """Aggregated metadata health state."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    """Return a shallow immutable metadata view."""

    return MappingProxyType(dict(values or {}))


@dataclass(frozen=True)
class Scope:
    """Tenant/workspace/framework isolation coordinates."""

    tenant: str = "default"
    workspace: str = "default"
    framework: str = "kernel"


@dataclass(frozen=True)
class Dependency:
    """A reference-only dependency edge."""

    target: str
    optional: bool = False


@dataclass(frozen=True)
class RegistryRecord:
    """Common metadata record stored by Hyper Kernel registries."""

    identifier: str
    version: str
    kind: str
    scope: Scope = Scope()
    dependencies: tuple[Dependency, ...] = ()
    capabilities: frozenset[str] = frozenset()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    lifecycle: str = "registered"
    health: HealthStatus = HealthStatus.UNKNOWN

    def __post_init__(self) -> None:
        invalid = not self.identifier or any(
            character.isspace() for character in self.identifier
        )
        if invalid:
            raise ValueError("identifier must be non-empty and contain no whitespace")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class Diagnostic:
    """Structured diagnostic metadata."""

    code: str
    message: str
    severity: str = "info"
    source: str = "kernel"
    scope: Scope = Scope()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


__all__ = (
    "Dependency",
    "Diagnostic",
    "FrameworkKind",
    "HealthStatus",
    "RegistryRecord",
    "Scope",
    "immutable_metadata",
)
