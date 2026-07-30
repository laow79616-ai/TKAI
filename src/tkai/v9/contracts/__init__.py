"""Immutable, execution-independent contracts for the V9 Adaptive Meta-Kernel."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return MappingProxyType(dict(values or {}))


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Lifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATING = "validating"
    READY = "ready"
    OBSERVING = "observing"
    ASSESSING = "assessing"
    PLANNING_REFERENCE = "planning_reference"
    REVIEWED = "reviewed"
    APPROVED_REFERENCE = "approved_reference"
    PAUSED = "paused"
    MAINTENANCE = "maintenance"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Scope:
    tenant: str = "default"
    workspace: str = "default"
    namespace: str = "tkai"


@dataclass(frozen=True)
class Reference:
    identifier: str
    version: str = "1.0.0"
    kind: str = "metadata"
    scope: Scope = Scope()
    dependencies: tuple[str, ...] = ()
    interfaces: tuple[str, ...] = ()
    permissions: frozenset[str] = frozenset({"read"})
    lifecycle: Lifecycle = Lifecycle.REGISTERED
    health: HealthStatus = HealthStatus.UNKNOWN
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(
            character.isspace() for character in self.identifier
        ):
            raise ValueError("identifier must be non-empty and contain no whitespace")
        if self.permissions - {"read", "observe", "assess", "plan-reference"}:
            raise ValueError("V9 references cannot contain executable permissions")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class TopologyEdge:
    source: str
    target: str
    kind: str = "dependency"
    required_version: str | None = None
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class Context:
    context_id: str
    scope: Scope = Scope()
    time_range: tuple[datetime, datetime] | None = None
    framework_references: tuple[str, ...] = ()
    capability_references: tuple[str, ...] = ()
    runtime_references: tuple[str, ...] = ()
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    health_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    version: str = "1.0.0"
    integrity_status: str = "unverified"
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "safe_metadata", immutable_metadata(self.safe_metadata)
        )


@dataclass(frozen=True)
class AdaptationProfile:
    adaptation_id: str
    context_reference: str
    subject_reference: str
    current_state_reference: str
    proposed_state_reference: str
    trigger_reference: str
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    risk_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    change_plan_reference: str | None = None
    review_reference: str | None = None
    approval_reference: str | None = None
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    version: str = "1.0.0"
    lifecycle: Lifecycle = Lifecycle.DRAFT
    audit_reference: str | None = None
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ChangePlan:
    change_plan_id: str
    subject_reference: str
    current_reference: str
    proposed_reference: str
    impacts: Mapping[str, object] = field(default_factory=immutable_metadata)
    rollback_reference: str | None = None
    validation_references: tuple[str, ...] = ()
    review_references: tuple[str, ...] = ()
    approval_references: tuple[str, ...] = ()
    risk_summary: str = ""
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    status: str = "draft"
    version: str = "1.0.0"
    audit_reference: str | None = None
    executable: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "impacts", immutable_metadata(self.impacts))


@dataclass(frozen=True)
class MetaKernelModel:
    kernel_id: str = "tkai-v9-adaptive-meta-kernel"
    kernel_name: str = "TKAI V9 Adaptive Meta-Kernel"
    kernel_version: str = "9.0.0"
    owner: str = "TKAI"
    namespace: str = "tkai.v9"
    registry_references: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    topology_reference: str = "v9:topology"
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    adaptation_references: tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.DRAFT
    health: HealthStatus = HealthStatus.UNKNOWN
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    tags: frozenset[str] = frozenset({"advisory", "reference-only", "local"})
    safe_metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "registry_references", immutable_metadata(self.registry_references)
        )
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(
            self, "safe_metadata", immutable_metadata(self.safe_metadata)
        )


__all__ = (
    "AdaptationProfile",
    "ChangePlan",
    "Context",
    "HealthStatus",
    "Lifecycle",
    "MetaKernelModel",
    "Reference",
    "Scope",
    "TopologyEdge",
    "immutable_metadata",
)
