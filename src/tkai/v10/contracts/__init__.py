"""Immutable contracts for the local-first TKAI V10 Sovereign Core."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Lifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATING = "validating"
    TRUSTED_REFERENCE = "trusted_reference"
    READY = "ready"
    OBSERVING = "observing"
    ASSESSING = "assessing"
    PLANNING_REFERENCE = "planning_reference"
    UNDER_REVIEW = "under_review"
    APPROVED_REFERENCE = "approved_reference"
    PAUSED = "paused"
    MAINTENANCE = "maintenance"
    DEGRADED_REFERENCE = "degraded_reference"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"
    DELETED = "deleted"


class PrincipalType(str, Enum):
    USER = "user"
    SERVICE = "service"
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    MODULE = "module"
    EXTENSION = "extension"
    RUNTIME = "runtime"
    SYSTEM = "system"
    TEST = "test"
    MOCK = "mock"


@dataclass(frozen=True)
class Scope:
    tenant: str = "local"
    workspace: str = "default"
    namespace: str = "tkai.v10"


@dataclass(frozen=True)
class Reference:
    identifier: str
    version: str = "10.0.0"
    kind: str = "metadata"
    scope: Scope = field(default_factory=Scope)
    integrity_reference: str | None = None
    attestation_reference: str | None = None


@dataclass(frozen=True)
class Principal:
    principal_id: str
    principal_type: PrincipalType
    identity_reference: str
    role_references: tuple[str, ...] = ()
    permission_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    lifecycle: Lifecycle = Lifecycle.REGISTERED
    integrity_status: str = "unknown"
    audit_reference: str | None = None


@dataclass(frozen=True)
class TrustDomain:
    trust_domain_id: str
    name: str
    scope: Scope = field(default_factory=Scope)
    principal_references: tuple[str, ...] = ()
    identity_references: tuple[str, ...] = ()
    policy_references: tuple[str, ...] = ()
    boundary_references: tuple[str, ...] = ()
    integrity_requirements: tuple[str, ...] = ()
    attestation_requirements: tuple[str, ...] = ()
    compatibility_requirements: tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.REGISTERED
    version: str = "10.0.0"
    audit_reference: str | None = None
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True)
class IntegrityRecord:
    integrity_id: str
    subject_reference: str
    integrity_type: str
    hash_algorithm_metadata: str = "sha256"
    expected_hash: str | None = None
    observed_hash_reference: str | None = None
    verification_status: str = "unverified"
    verification_time: datetime | None = None
    evidence_references: tuple[str, ...] = ()
    version: str = "10.0.0"
    audit_reference: str | None = None


@dataclass(frozen=True)
class Attestation:
    attestation_id: str
    subject_reference: str
    attestation_type: str
    issuer_reference: str
    evidence_references: tuple[str, ...] = ()
    integrity_reference: str | None = None
    policy_references: tuple[str, ...] = ()
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    status: str = "registered"
    version: str = "10.0.0"
    audit_reference: str | None = None
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True)
class Boundary:
    boundary_id: str
    boundary_type: str
    scope: Scope = field(default_factory=Scope)
    allowed_references: tuple[str, ...] = ()
    restricted_references: tuple[str, ...] = ()
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    version: str = "10.0.0"
    lifecycle: Lifecycle = Lifecycle.REGISTERED
    audit_reference: str | None = None


@dataclass(frozen=True)
class Context:
    context_id: str
    scope: Scope = field(default_factory=Scope)
    time_range: tuple[datetime, datetime] | None = None
    framework_references: tuple[str, ...] = ()
    capability_references: tuple[str, ...] = ()
    service_references: tuple[str, ...] = ()
    runtime_references: tuple[str, ...] = ()
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    boundary_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    attestation_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    version: str = "10.0.0"
    integrity_status: str = "unknown"
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    audit_reference: str | None = None


@dataclass(frozen=True)
class ChangePlan:
    change_plan_id: str
    subject_reference: str
    current_reference: str
    proposed_reference: str
    impacts: Mapping[str, str] = field(default_factory=lambda: MappingProxyType({}))
    rollback_reference: str | None = None
    validation_references: tuple[str, ...] = ()
    review_references: tuple[str, ...] = ()
    approval_references: tuple[str, ...] = ()
    risk_summary: str = ""
    confidence: float = 0.0
    limitations: tuple[str, ...] = ()
    status: str = "draft"
    version: str = "10.0.0"
    audit_reference: str | None = None
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class TopologyEdge:
    source: str
    target: str
    kind: str = "dependency"
    required_version: str | None = None


@dataclass(frozen=True)
class SovereignCoreModel:
    core_id: str = "tkai-v10-sovereign-core"
    core_name: str = "TKAI V10 Sovereign Core"
    core_version: str = "10.0.0"
    owner: str = "TKAI"
    namespace: str = "tkai.v10.sovereign_core"
    trust_domain_reference: str = "v10:trust-domain:local"
    registry_references: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    boundary_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    attestation_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    change_plan_references: tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.REGISTERED
    health: str = "healthy"
    metrics: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    audit: tuple[str, ...] = ()
    tags: frozenset[str] = frozenset(
        {"local-first", "metadata-driven", "advisory", "bounded", "reference-only"}
    )
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)


__all__ = (
    "Attestation",
    "Boundary",
    "ChangePlan",
    "Context",
    "IntegrityRecord",
    "Lifecycle",
    "Principal",
    "PrincipalType",
    "Reference",
    "Scope",
    "SovereignCoreModel",
    "TopologyEdge",
    "TrustDomain",
)
