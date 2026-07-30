"""Immutable contracts for the advisory V9 Adaptive Governance Mesh."""

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


class GovernanceLifecycle(str, Enum):
    """Lifecycle of governance metadata, never runtime execution."""

    DRAFT = "draft"
    REGISTERED = "registered"
    IN_REVIEW = "in-review"
    REVIEWED = "reviewed"
    APPROVED_METADATA = "approved-metadata"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class GovernanceScope:
    """Isolation coordinates attached to every governed reference."""

    tenant: str = "default"
    workspace: str = "default"
    capability: str = "*"
    framework: str = "*"
    module: str = "*"
    extension: str = "*"
    configuration: str = "*"


@dataclass(frozen=True)
class GovernanceReference:
    """Reference to metadata owned by another framework or module."""

    identifier: str
    version: str = ""
    uri: str = ""
    kind: str = "metadata"
    generation: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        if self.generation.lower() not in {"", "v6", "v7", "v8", "v9"}:
            raise ValueError("reference generation must be V6, V7, V8, or V9")
        object.__setattr__(self, "generation", self.generation.lower())
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class GovernanceProfile:
    """Complete cross-framework governance metadata profile."""

    profile_id: str
    version: str
    owner: str
    framework_references: tuple[GovernanceReference, ...] = ()
    policy_references: tuple[GovernanceReference, ...] = ()
    constraint_references: tuple[GovernanceReference, ...] = ()
    compliance_references: tuple[GovernanceReference, ...] = ()
    boundary_references: tuple[GovernanceReference, ...] = ()
    review_references: tuple[GovernanceReference, ...] = ()
    approval_references: tuple[GovernanceReference, ...] = ()
    compatibility_references: tuple[GovernanceReference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: GovernanceScope = GovernanceScope()
    lifecycle: GovernanceLifecycle = GovernanceLifecycle.DRAFT

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version or not self.owner:
            raise ValueError("profile_id, version, and owner are required")
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(item) for item in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class PolicyRecord:
    """Policy relationship metadata without enforcement semantics."""

    policy_id: str
    name: str
    framework_references: tuple[GovernanceReference, ...] = ()
    rule_references: tuple[GovernanceReference, ...] = ()
    constraint_references: tuple[GovernanceReference, ...] = ()
    compliance_references: tuple[GovernanceReference, ...] = ()
    version: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.policy_id or not self.name:
            raise ValueError("policy_id and name are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))

    @property
    def enforced(self) -> bool:
        return False


@dataclass(frozen=True)
class ConstraintRecord:
    """Advisory constraint metadata."""

    constraint_id: str
    name: str
    policy_references: tuple[GovernanceReference, ...] = ()
    boundary_references: tuple[GovernanceReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.constraint_id or not self.name:
            raise ValueError("constraint_id and name are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class BoundaryRecord:
    """Reference-only runtime boundary metadata."""

    boundary_id: str
    boundary_type: str
    scope: GovernanceScope = GovernanceScope()
    references: tuple[GovernanceReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        supported = {
            "tenant",
            "workspace",
            "capability",
            "framework",
            "module",
            "extension",
            "configuration",
        }
        if not self.boundary_id or self.boundary_type not in supported:
            raise ValueError("boundary_id and a supported boundary_type are required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class ReviewRecord:
    """Review metadata, findings, and non-executing recommendations."""

    review_id: str
    reviewer_references: tuple[GovernanceReference, ...] = ()
    findings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    status: str = "pending"
    audit_references: tuple[GovernanceReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.review_id:
            raise ValueError("review_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class ApprovalRecord:
    """Approval metadata that can never authorize runtime execution."""

    approval_id: str
    subject_reference: GovernanceReference
    approver_references: tuple[GovernanceReference, ...] = ()
    status: str = "pending"
    review_references: tuple[GovernanceReference, ...] = ()
    audit_references: tuple[GovernanceReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.approval_id:
            raise ValueError("approval_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class ComplianceRecord:
    """Coverage metadata only; no compliance enforcement runtime exists."""

    compliance_id: str
    summary: str = ""
    policy_coverage: float = 0.0
    constraint_coverage: float = 0.0
    compatibility_coverage: float = 0.0
    review_coverage: float = 0.0
    approval_coverage: float = 0.0
    audit_coverage: float = 0.0
    references: tuple[GovernanceReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.compliance_id:
            raise ValueError("compliance_id is required")
        coverages = (
            self.policy_coverage,
            self.constraint_coverage,
            self.compatibility_coverage,
            self.review_coverage,
            self.approval_coverage,
            self.audit_coverage,
        )
        if any(value < 0 or value > 1 for value in coverages):
            raise ValueError("coverage values must be between 0 and 1")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class CompatibilityRecord:
    """Cross-version V6/V7/V8/V9 governance compatibility metadata."""

    compatibility_id: str
    source: GovernanceReference
    target: GovernanceReference
    status: str = "compatible"
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.compatibility_id:
            raise ValueError("compatibility_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


Reference = GovernanceReference

__all__ = (
    "ApprovalRecord",
    "BoundaryRecord",
    "CompatibilityRecord",
    "ComplianceRecord",
    "ConstraintRecord",
    "GovernanceLifecycle",
    "GovernanceProfile",
    "GovernanceReference",
    "GovernanceScope",
    "PolicyRecord",
    "Reference",
    "ReviewRecord",
    "immutable_metadata",
)

