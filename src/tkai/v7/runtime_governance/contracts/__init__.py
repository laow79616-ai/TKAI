"""Immutable contracts for advisory V7 runtime governance metadata."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Any

MAX_REFERENCES = 256
_SECRET_WORDS = ("password", "secret", "token", "cookie", "session", "api_key")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def safe_metadata(value: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
    """Return bounded scalar metadata and reject likely secret material."""
    data = dict(value or {})
    if len(data) > 128:
        raise ValueError("metadata exceeds bounded capacity")
    for key, item in data.items():
        if any(word in key.lower() for word in _SECRET_WORDS):
            raise ValueError(f"unsafe metadata field: {key}")
        if isinstance(item, (dict, list, tuple, set)) or len(str(item)) > 512:
            raise ValueError("metadata values must be bounded scalars")
    return MappingProxyType(data)


def _bounded(values: tuple[str, ...]) -> None:
    if len(values) > MAX_REFERENCES:
        raise ValueError("reference collection exceeds bounded capacity")


class Lifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    VALIDATING = "validating"
    READY = "ready"
    REVIEW = "review"
    APPROVED_REFERENCE = "approved-reference"
    PAUSED = "paused"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"
    DELETED = "deleted"


class EligibilityKind(str, Enum):
    CAPABILITY = "capability"
    WORKFLOW = "workflow"
    SERVICE = "service"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"


class BoundaryKind(str, Enum):
    TENANT = "tenant"
    WORKSPACE = "workspace"
    CAPABILITY = "capability"
    MODULE = "module"
    EXTENSION = "extension"
    CONFIGURATION = "configuration"
    EVENT = "event"
    SERVICE = "service"


class PauseKind(str, Enum):
    WORKSPACE = "workspace"
    CAPABILITY = "capability"
    MAINTENANCE = "maintenance"
    EMERGENCY = "emergency"


@dataclass(frozen=True)
class Scope:
    tenant: str
    workspace: str
    namespace: str = "runtime-governance"

    def __post_init__(self) -> None:
        values = (self.tenant, self.workspace, self.namespace)
        if not all(values) or any(len(value) > 128 for value in values):
            raise ValueError("bounded tenant, workspace, and namespace are required")


@dataclass(frozen=True)
class VersionMetadata:
    version: str = "1.0.0"
    compatibility_references: tuple[str, ...] = ("v6",)
    change_reference: str | None = None
    deprecated: bool = False


@dataclass(frozen=True)
class GovernanceProfile:
    profile_id: str
    name: str
    scope: Scope
    owner: str
    version: VersionMetadata = field(default_factory=VersionMetadata)
    lifecycle: Lifecycle = Lifecycle.DRAFT
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    runtime_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, Any] = field(default_factory=safe_metadata)
    audit_reference: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=safe_metadata)

    @property
    def namespace(self) -> str:
        return self.scope.namespace

    @property
    def tenant(self) -> str:
        return self.scope.tenant

    @property
    def workspace(self) -> str:
        return self.scope.workspace

    def __post_init__(self) -> None:
        for references in (
            self.policy_references,
            self.constraint_references,
            self.runtime_references,
        ):
            _bounded(references)
        object.__setattr__(self, "metrics", safe_metadata(self.metrics))
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))


@dataclass(frozen=True)
class GovernancePolicy:
    policy_id: str
    name: str
    scope: Scope
    runtime_metadata: Mapping[str, Any] = field(default_factory=safe_metadata)
    eligibility_metadata: Mapping[str, Any] = field(default_factory=safe_metadata)
    maintenance_metadata: Mapping[str, Any] = field(default_factory=safe_metadata)
    pause_metadata: Mapping[str, Any] = field(default_factory=safe_metadata)
    killswitch_metadata: Mapping[str, Any] = field(default_factory=safe_metadata)
    compatibility_metadata: Mapping[str, Any] = field(default_factory=safe_metadata)
    version_metadata: VersionMetadata = field(default_factory=VersionMetadata)
    review_references: tuple[str, ...] = ()
    approval_references: tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.DRAFT
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.execution_authorized:
            raise ValueError("governance policies never authorize execution")
        for name in (
            "runtime_metadata",
            "eligibility_metadata",
            "maintenance_metadata",
            "pause_metadata",
            "killswitch_metadata",
            "compatibility_metadata",
        ):
            object.__setattr__(self, name, safe_metadata(getattr(self, name)))


@dataclass(frozen=True)
class GovernanceConstraint:
    constraint_id: str
    kind: str
    subject_reference: str
    rule_references: tuple[str, ...]
    scope: Scope
    required: bool = True


@dataclass(frozen=True)
class RuntimeBoundary:
    boundary_id: str
    kind: BoundaryKind
    subject_reference: str
    scope: Scope
    isolation_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ("v6",)
    advisory_only: bool = True

    def __post_init__(self) -> None:
        if not self.advisory_only:
            raise ValueError("runtime boundaries are advisory metadata")


@dataclass(frozen=True)
class RuntimeReference:
    runtime_id: str
    name: str
    scope: Scope
    capability_references: tuple[str, ...] = ()
    service_references: tuple[str, ...] = ()
    configuration_references: tuple[str, ...] = ()
    boundary_references: tuple[str, ...] = ()
    lifecycle: Lifecycle = Lifecycle.REGISTERED
    readiness: bool = False
    executable: bool = False

    def __post_init__(self) -> None:
        if self.executable:
            raise ValueError("runtime references are non-executable metadata")


@dataclass(frozen=True)
class EligibilityRequest:
    assessment_id: str
    kind: EligibilityKind
    subject_reference: str
    scope: Scope
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    runtime_reference: str | None = None


@dataclass(frozen=True)
class EligibilityAssessment:
    assessment_id: str
    kind: EligibilityKind
    subject_reference: str
    scope: Scope
    eligible: bool
    reasons: tuple[str, ...]
    policy_references: tuple[str, ...]
    constraint_references: tuple[str, ...]
    evaluated_at: datetime = field(default_factory=utc_now)
    read_only: bool = True
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if not self.read_only or self.execution_authorized:
            raise ValueError("eligibility is read-only and never authorizes execution")


@dataclass(frozen=True)
class PauseMetadata:
    pause_id: str
    kind: PauseKind
    subject_reference: str
    reason: str
    scope: Scope
    active: bool = False
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    review_reference: str | None = None
    audit_reference: str | None = None
    runtime_mutated: bool = False

    def __post_init__(self) -> None:
        if self.runtime_mutated:
            raise ValueError("pause metadata cannot mutate runtime state")


@dataclass(frozen=True)
class MaintenanceMetadata:
    maintenance_id: str
    subject_reference: str
    reason: str
    scope: Scope
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    readiness_impact: str = "review-required"


@dataclass(frozen=True)
class ActivationRecord:
    activation_id: str
    activated: bool
    reason: str
    scope_reference: str
    review_reference: str | None
    audit_reference: str | None
    recorded_at: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class KillSwitchMetadata:
    killswitch_id: str
    name: str
    subject_reference: str
    reason: str
    scope: Scope
    active: bool = False
    activation_history: tuple[ActivationRecord, ...] = ()
    review_reference: str | None = None
    audit_reference: str | None = None
    runtime_mutated: bool = False

    def __post_init__(self) -> None:
        if self.runtime_mutated:
            raise ValueError("kill-switch metadata cannot mutate runtime state")


@dataclass(frozen=True)
class ReviewMetadata:
    review_id: str
    subject_reference: str
    reviewer: str
    findings: tuple[str, ...]
    status: str
    scope: Scope
    audit_reference: str | None = None


@dataclass(frozen=True)
class ApprovalReference:
    approval_id: str
    subject_reference: str
    approver: str
    decision: str
    scope: Scope
    conditions: tuple[str, ...] = ()
    execution_authorized: bool = False

    def __post_init__(self) -> None:
        if self.execution_authorized:
            raise ValueError("approval references never authorize execution")


@dataclass(frozen=True)
class Diagnostic:
    diagnostic_id: str
    category: str
    code: str
    severity: str
    summary: str
    scope: Scope
    subject_reference: str | None = None
    remediation_references: tuple[str, ...] = ()
    safe: bool = True


def serialize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serialize(item) for item in value]
    if hasattr(value, "__dataclass_fields__"):
        return {
            item.name: serialize(getattr(value, item.name)) for item in fields(value)
        }
    return value


__all__ = tuple(name for name in globals() if not name.startswith("_"))
