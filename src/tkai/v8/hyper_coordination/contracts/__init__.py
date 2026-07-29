"""Immutable contracts for the advisory V8 Hyper Coordination Framework."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    """Copy metadata into a read-only mapping."""

    return MappingProxyType(dict(values or {}))


class CoordinationLifecycle(str, Enum):
    """Reference lifecycle; approval never grants execution authority."""

    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATED = "validated"
    READY = "ready"
    SYNCHRONIZED = "synchronized"
    REVIEWED = "reviewed"
    APPROVED_REFERENCE = "approved_reference"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass(frozen=True)
class CoordinationScope:
    """Tenant, workspace, and framework isolation coordinates."""

    tenant: str = "default"
    workspace: str = "default"
    framework: str = "hyper-coordination"


@dataclass(frozen=True)
class Reference:
    """Governed reference to metadata owned by another framework."""

    identifier: str
    version: str = ""
    uri: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class CoordinationProfile:
    """Complete metadata profile used for cross-framework coordination."""

    profile_id: str
    name: str
    description: str
    version: str
    owner: str
    framework_references: tuple[Reference, ...] = ()
    capability_references: tuple[Reference, ...] = ()
    dependency_references: tuple[Reference, ...] = ()
    relationship_references: tuple[Reference, ...] = ()
    lifecycle: CoordinationLifecycle = CoordinationLifecycle.DRAFT
    compatibility: tuple[Reference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: CoordinationScope = CoordinationScope()

    def __post_init__(self) -> None:
        if not self.profile_id or not self.name or not self.version:
            raise ValueError("profile_id, name, and version are required")
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(item) for item in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        """Approval is reference-only and can never authorize execution."""

        return False


@dataclass(frozen=True)
class FrameworkDescriptor:
    """Versioned reference for V6, V7, V8, or a future framework."""

    identifier: str
    version: str
    generation: str
    capabilities: tuple[str, ...] = ()
    lifecycle: CoordinationLifecycle = CoordinationLifecycle.REGISTERED
    compatibility: tuple[str, ...] = ()
    health: str = "unknown"
    scope: CoordinationScope = CoordinationScope()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


class GraphKind(str, Enum):
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    RELATIONSHIP = "relationship"
    COMPATIBILITY = "compatibility"
    LIFECYCLE = "lifecycle"
    HEALTH = "health"


@dataclass(frozen=True)
class CoordinationEdge:
    """Directed reference edge. There is deliberately no execution edge kind."""

    source: str
    target: str
    kind: GraphKind
    relationship: str = "depends_on"
    optional: bool = False
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.source or not self.target:
            raise ValueError("edge source and target are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class SynchronizationRecord:
    """A computed metadata synchronization proposal, never a runtime operation."""

    synchronization_id: str
    category: str
    source: Reference
    target: Reference
    status: str = "pending"
    changes: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: CoordinationScope = CoordinationScope()

    def __post_init__(self) -> None:
        allowed = {"metadata", "lifecycle", "compatibility", "version", "diagnostics"}
        if self.category not in allowed:
            raise ValueError(f"unsupported synchronization category: {self.category}")
        object.__setattr__(self, "changes", immutable_metadata(self.changes))


@dataclass(frozen=True)
class GovernanceReferences:
    """External governance evidence attached by reference."""

    policies: tuple[Reference, ...] = ()
    approvals: tuple[Reference, ...] = ()
    risks: tuple[Reference, ...] = ()
    compatibility: tuple[Reference, ...] = ()
    reviews: tuple[Reference, ...] = ()
    audits: tuple[Reference, ...] = ()


__all__ = (
    "CoordinationEdge",
    "CoordinationLifecycle",
    "CoordinationProfile",
    "CoordinationScope",
    "FrameworkDescriptor",
    "GovernanceReferences",
    "GraphKind",
    "Reference",
    "SynchronizationRecord",
    "immutable_metadata",
)
