"""Immutable metadata contracts for the TKAI V10 Sovereign Governance Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from tkai.v10.contracts import Scope


class SubjectType(str, Enum):
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    SERVICE = "service"
    MODULE = "module"
    EXTENSION = "extension"
    RUNTIME_REFERENCE = "runtime_reference"
    CONFIGURATION = "configuration"
    STORAGE = "storage"
    API = "api"
    DASHBOARD = "dashboard"
    AI_STUDIO = "ai_studio"
    RELEASE = "release"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"


class GovernanceDomain(str, Enum):
    FRAMEWORK = "framework"
    CAPABILITY = "capability"
    SERVICE = "service"
    MODULE = "module"
    EXTENSION = "extension"
    RUNTIME_REFERENCE = "runtime_reference"
    CONFIGURATION = "configuration"
    STORAGE = "storage"
    API = "api"
    DASHBOARD = "dashboard"
    AI_STUDIO = "ai_studio"
    RELEASE = "release"
    DEPLOYMENT = "deployment"
    DOCUMENTATION = "documentation"


class PolicyStatus(str, Enum):
    REQUIRED = "required"
    ADVISORY = "advisory"
    CONDITIONAL = "conditional"
    DEPRECATED = "deprecated"


class ConstraintType(str, Enum):
    VERSION = "version"
    COMPATIBILITY = "compatibility"
    SECURITY = "security"
    BOUNDARY = "boundary"
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    RUNTIME = "runtime"
    RELEASE = "release"
    DOCUMENTATION = "documentation"


class ReviewStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    REJECTED = "rejected"
    DEFERRED = "deferred"


class ApprovalStatus(str, Enum):
    REQUIRED = "required"
    RECORDED = "recorded"
    MISSING = "missing"
    WAIVED = "waived"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceDomain(str, Enum):
    SECURITY = "security"
    COMPATIBILITY = "compatibility"
    INTEGRITY = "integrity"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    RELEASE = "release"
    GOVERNANCE = "governance"


class RelationshipType(str, Enum):
    GOVERNS = "governs"
    REVIEWS = "reviews"
    DEPENDS_ON = "depends_on"
    REFERENCES = "references"
    CONSTRAINS = "constrains"
    VALIDATES = "validates"


class ValidationType(str, Enum):
    POLICY = "policy_validation"
    CONSTRAINT = "constraint_validation"
    COMPATIBILITY = "compatibility_validation"
    RISK = "risk_validation"
    COMPLIANCE = "compliance_validation"
    GOVERNANCE = "governance_validation"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class GovernanceProfile:
    profile_id: str
    subject_reference: str
    subject_type: SubjectType
    governance_domain: GovernanceDomain
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    review_references: tuple[str, ...] = ()
    approval_references: tuple[str, ...] = ()
    risk_references: tuple[str, ...] = ()
    compliance_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=lambda: MappingProxyType({}))
    safe_metadata: Mapping[str, object] = field(
        default_factory=lambda: MappingProxyType({})
    )
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class GovernanceDomainRecord:
    domain_id: str
    domain: GovernanceDomain
    subject_reference: str
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class PolicyReference:
    policy_id: str
    subject_reference: str
    status: PolicyStatus
    reference: str
    scope: Scope = field(default_factory=Scope)
    executable: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ConstraintReference:
    constraint_id: str
    subject_reference: str
    constraint_type: ConstraintType
    reference: str
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class ReviewReference:
    review_id: str
    subject_reference: str
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer_reference: str | None = None
    evidence_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    workflow_execution: bool = field(default=False, init=False)


@dataclass(frozen=True)
class ApprovalReference:
    approval_id: str
    subject_reference: str
    status: ApprovalStatus = ApprovalStatus.REQUIRED
    approver_reference: str | None = None
    evidence_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    automatic_approval: bool = field(default=False, init=False)


@dataclass(frozen=True)
class RiskReference:
    risk_id: str
    subject_reference: str
    level: RiskLevel
    evidence_references: tuple[str, ...] = ()
    mitigation_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class ComplianceReference:
    compliance_id: str
    subject_reference: str
    domain: ComplianceDomain
    reference: str
    evidence_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class GovernanceRelationship:
    relationship_id: str
    source_reference: str
    target_reference: str
    relationship_type: RelationshipType
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class CompatibilityGovernance:
    compatibility_id: str
    source_generation: str
    subject_reference: str
    target_generation: str = "v10"
    validation_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    migration: bool = field(default=False, init=False)
    upgrade: bool = field(default=False, init=False)
    rollback: bool = field(default=False, init=False)


@dataclass(frozen=True)
class GovernanceValidation:
    validation_id: str
    subject_reference: str
    validation_type: ValidationType
    status: ValidationStatus = ValidationStatus.UNKNOWN
    evidence_references: tuple[str, ...] = ()
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


__all__ = (
    "ApprovalReference",
    "ApprovalStatus",
    "CompatibilityGovernance",
    "ComplianceDomain",
    "ComplianceReference",
    "ConstraintReference",
    "ConstraintType",
    "GovernanceDomain",
    "GovernanceDomainRecord",
    "GovernanceProfile",
    "GovernanceRelationship",
    "GovernanceValidation",
    "PolicyReference",
    "PolicyStatus",
    "RelationshipType",
    "ReviewReference",
    "ReviewStatus",
    "RiskLevel",
    "RiskReference",
    "SubjectType",
    "ValidationStatus",
    "ValidationType",
)
