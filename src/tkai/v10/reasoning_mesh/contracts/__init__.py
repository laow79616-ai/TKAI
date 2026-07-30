"""Immutable safe-metadata contracts for the V10 Sovereign Reasoning Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from tkai.v10.contracts import Scope


def _metadata() -> Mapping[str, object]:
    return MappingProxyType({})


def _metrics() -> Mapping[str, float]:
    return MappingProxyType({})


class ClaimType(str, Enum):
    OBSERVATIONAL = "observational"
    DERIVED = "derived"
    COMPARATIVE = "comparative"
    COMPATIBILITY = "compatibility"
    INTEGRITY = "integrity"
    TRUST = "trust"
    GOVERNANCE = "governance"
    SECURITY = "security"
    OPERATIONAL_REFERENCE = "operational_reference"
    DIAGNOSTIC = "diagnostic"
    HEALTH = "health"
    RISK = "risk"
    LIMITATION = "limitation"


class InferenceType(str, Enum):
    DEDUCTIVE_REFERENCE = "deductive_reference"
    INDUCTIVE_REFERENCE = "inductive_reference"
    COMPARATIVE_REFERENCE = "comparative_reference"
    COMPATIBILITY_REFERENCE = "compatibility_reference"
    INTEGRITY_REFERENCE = "integrity_reference"
    TRUST_REFERENCE = "trust_reference"
    GOVERNANCE_REFERENCE = "governance_reference"
    DIAGNOSTIC_REFERENCE = "diagnostic_reference"
    RISK_REFERENCE = "risk_reference"
    CONSTRAINT_REFERENCE = "constraint_reference"


class UncertaintyType(str, Enum):
    KNOWN = "known"
    PARTIALLY_KNOWN = "partially_known"
    UNKNOWN = "unknown"
    CONFLICTING = "conflicting"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    OUTDATED_REFERENCE = "outdated_reference"
    UNVERIFIED_REFERENCE = "unverified_reference"
    UNSUPPORTED = "unsupported"


class ContradictionType(str, Enum):
    CLAIM_CONFLICT = "claim_conflict"
    EVIDENCE_CONFLICT = "evidence_conflict"
    VERSION_CONFLICT = "version_conflict"
    COMPATIBILITY_CONFLICT = "compatibility_conflict"
    INTEGRITY_CONFLICT = "integrity_conflict"
    TRUST_CONFLICT = "trust_conflict"
    GOVERNANCE_CONFLICT = "governance_conflict"
    SECURITY_CONFLICT = "security_conflict"
    CONFIGURATION_CONFLICT = "configuration_conflict"
    RUNTIME_REFERENCE_CONFLICT = "runtime_reference_conflict"


class ConstraintType(str, Enum):
    SECURITY = "security"
    GOVERNANCE = "governance"
    COMPATIBILITY = "compatibility"
    INTEGRITY = "integrity"
    TRUST = "trust"
    BOUNDARY = "boundary"
    RUNTIME = "runtime"
    CONFIGURATION = "configuration"
    STORAGE = "storage"
    API = "api"
    DEPLOYMENT = "deployment"
    OPERATIONAL = "operational"
    TIME = "time"
    RESULT_SIZE = "result_size"
    SOURCE_COUNT = "source_count"


@dataclass(frozen=True)
class ReasoningProfile:
    profile_id: str
    subject_reference: str
    context_references: tuple[str, ...] = ()
    claim_references: tuple[str, ...] = ()
    premise_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    inference_references: tuple[str, ...] = ()
    assumption_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    alternative_references: tuple[str, ...] = ()
    confidence_references: tuple[str, ...] = ()
    uncertainty_references: tuple[str, ...] = ()
    contradiction_references: tuple[str, ...] = ()
    explanation_references: tuple[str, ...] = ()
    assessment_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    governance_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    knowledge_references: tuple[str, ...] = ()
    validation_references: tuple[str, ...] = ()
    audit_references: tuple[str, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, float] = field(default_factory=_metrics)
    safe_metadata: Mapping[str, object] = field(default_factory=_metadata)
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class ReasoningContext:
    context_id: str
    subject_reference: str
    context_scope: str
    tenant_reference: str = ""
    workspace_reference: str = ""
    namespace: str = "default"
    time_range: tuple[str, str] | None = None
    knowledge_references: tuple[str, ...] = ()
    policy_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    boundary_references: tuple[str, ...] = ()
    integrity_references: tuple[str, ...] = ()
    trust_references: tuple[str, ...] = ()
    compatibility_references: tuple[str, ...] = ()
    version: str = "10.0.0"
    status: str = "registered"
    safe_metadata: Mapping[str, object] = field(default_factory=_metadata)
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Claim:
    claim_id: str
    statement_summary: str
    subject_reference: str
    claim_type: ClaimType
    status: str = "registered"
    evidence_references: tuple[str, ...] = ()
    premise_references: tuple[str, ...] = ()
    assumption_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    confidence: float | None = None
    uncertainty: UncertaintyType = UncertaintyType.UNKNOWN
    contradiction_references: tuple[str, ...] = ()
    version: str = "10.0.0"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Premise:
    premise_id: str
    summary: str
    source_reference: str
    evidence_references: tuple[str, ...] = ()
    integrity_reference: str | None = None
    trust_reference: str | None = None
    compatibility_reference: str | None = None
    status: str = "registered"
    version: str = "10.0.0"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class EvidenceReference:
    evidence_id: str
    source_reference: str
    subject_reference: str
    integrity_reference: str | None = None
    trust_reference: str | None = None
    compatibility_reference: str | None = None
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Inference:
    inference_id: str
    inference_type: InferenceType
    premise_references: tuple[str, ...]
    evidence_references: tuple[str, ...]
    result_claim_reference: str
    rule_reference: str
    constraint_references: tuple[str, ...] = ()
    confidence: float | None = None
    uncertainty: UncertaintyType = UncertaintyType.UNKNOWN
    limitations: tuple[str, ...] = ()
    status: str = "recorded"
    version: str = "10.0.0"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Assumption:
    assumption_id: str
    summary: str
    assumption_scope: str
    source_reference: str
    validation_status: str = "unverified"
    risk_level: str = "unknown"
    confidence: float | None = None
    expiration_reference: str | None = None
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class ConstraintReference:
    constraint_id: str
    constraint_type: ConstraintType
    reference: str
    summary: str = ""
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    metadata_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Alternative:
    alternative_id: str
    summary: str
    claim_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    compatibility_impact: str = "unknown"
    integrity_impact: str = "unknown"
    trust_impact: str = "unknown"
    governance_impact: str = "unknown"
    security_impact: str = "unknown"
    risk_summary: str = ""
    confidence: float | None = None
    limitations: tuple[str, ...] = ()
    status: str = "advisory"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Confidence:
    confidence_id: str
    value: float | None
    band: str
    evidence_coverage: str
    source_quality_reference: str | None = None
    integrity_status: str = "unknown"
    trust_status: str = "unknown"
    compatibility_status: str = "unknown"
    contradiction_count: int = 0
    limitation_count: int = 0
    explanation_reference: str | None = None
    scope: Scope = field(default_factory=Scope)


@dataclass(frozen=True)
class Contradiction:
    contradiction_id: str
    contradiction_type: ContradictionType
    left_reference: str
    right_reference: str
    summary: str
    status: str = "unresolved"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    automatic_resolution: bool = field(default=False, init=False)


@dataclass(frozen=True)
class Explanation:
    explanation_id: str
    summary: str
    supporting_claim_references: tuple[str, ...] = ()
    evidence_references: tuple[str, ...] = ()
    assumption_references: tuple[str, ...] = ()
    constraint_references: tuple[str, ...] = ()
    alternative_references: tuple[str, ...] = ()
    confidence_summary: str = ""
    uncertainty_summary: str = ""
    contradiction_summary: str = ""
    limitations: tuple[str, ...] = ()
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    safe_user_facing_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class Assessment:
    assessment_id: str
    assessment_type: str
    subject_reference: str
    summary: str
    reference_ids: tuple[str, ...] = ()
    status: str = "advisory"
    audit_reference: str | None = None
    scope: Scope = field(default_factory=Scope)
    advisory_only: bool = field(default=True, init=False)


@dataclass(frozen=True)
class CompatibilityReference:
    compatibility_id: str
    generation: str
    subject_reference: str
    version: str = "10.0.0"
    scope: Scope = field(default_factory=Scope)
    reference_only: bool = field(default=True, init=False)


__all__ = (
    "Alternative",
    "Assessment",
    "Assumption",
    "Claim",
    "ClaimType",
    "CompatibilityReference",
    "Confidence",
    "ConstraintReference",
    "ConstraintType",
    "Contradiction",
    "ContradictionType",
    "EvidenceReference",
    "Explanation",
    "Inference",
    "InferenceType",
    "Premise",
    "ReasoningContext",
    "ReasoningProfile",
    "UncertaintyType",
)
