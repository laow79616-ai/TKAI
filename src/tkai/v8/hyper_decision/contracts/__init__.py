"""Immutable metadata contracts for the advisory V8 Hyper Decision Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

_FORBIDDEN = frozenset(
    {"execute", "execution", "runtime_action", "automatic_approval", "tiktok_action"}
)


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return MappingProxyType(dict(values or {}))


def reject_executable_metadata(values: Mapping[str, object]) -> None:
    for key, value in values.items():
        if str(key).lower() in _FORBIDDEN:
            raise ValueError("executable and automatic approval metadata is prohibited")
        if isinstance(value, Mapping):
            reject_executable_metadata(value)


class DecisionLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    EVALUATED = "evaluated"
    REVIEWED = "reviewed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class DecisionScope:
    tenant: str = "default"
    workspace: str = "default"
    decision_namespace: str = "default"


@dataclass(frozen=True)
class DecisionReference:
    identifier: str
    version: str = ""
    uri: str = ""
    kind: str = "metadata"
    generation: str = ""
    framework: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        if self.generation not in {"", "v6", "v7", "v8"}:
            raise ValueError("reference generation must be V6, V7, or V8")
        reject_executable_metadata(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class DecisionProfile:
    profile_id: str
    version: str
    owner: str
    decision_references: tuple[DecisionReference, ...] = ()
    alternative_references: tuple[DecisionReference, ...] = ()
    evidence_references: tuple[DecisionReference, ...] = ()
    knowledge_references: tuple[DecisionReference, ...] = ()
    reasoning_references: tuple[DecisionReference, ...] = ()
    recommendation_references: tuple[DecisionReference, ...] = ()
    governance_references: tuple[DecisionReference, ...] = ()
    compatibility_references: tuple[DecisionReference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: DecisionScope = DecisionScope()
    lifecycle: DecisionLifecycle = DecisionLifecycle.DRAFT

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version or not self.owner:
            raise ValueError("profile_id, version, and owner are required")
        reject_executable_metadata(self.metadata)
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(x) for x in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class DecisionMetadata:
    decision_id: str
    summary: str
    classification: str
    evidence_references: tuple[DecisionReference, ...] = ()
    recommendation_references: tuple[DecisionReference, ...] = ()
    evaluation_references: tuple[DecisionReference, ...] = ()
    confidence_reference: DecisionReference | None = None
    review_references: tuple[DecisionReference, ...] = ()
    approval_references: tuple[DecisionReference, ...] = ()
    version_history: tuple[Mapping[str, object], ...] = ()
    explainability_summary: str = ""
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: DecisionScope = DecisionScope()

    def __post_init__(self) -> None:
        if not self.decision_id or not self.summary or not self.classification:
            raise ValueError("decision_id, summary, and classification are required")
        reject_executable_metadata(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self,
            "version_history",
            tuple(immutable_metadata(x) for x in self.version_history),
        )

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class AlternativeMetadata:
    alternative_id: str
    summary: str
    expected_outcomes: tuple[str, ...] = ()
    risk_summaries: tuple[str, ...] = ()
    constraint_references: tuple[DecisionReference, ...] = ()
    evidence_references: tuple[DecisionReference, ...] = ()
    comparison_references: tuple[DecisionReference, ...] = ()
    scope: DecisionScope = DecisionScope()


class ComparisonKind(str, Enum):
    DECISION = "decision-vs-decision"
    ALTERNATIVE = "alternative-vs-alternative"
    HISTORICAL = "historical"
    EVIDENCE = "evidence"
    CONFIDENCE = "confidence"
    GOVERNANCE = "governance"
    COMPATIBILITY = "compatibility"


@dataclass(frozen=True)
class ComparisonMetadata:
    comparison_id: str
    kind: ComparisonKind
    left_reference: DecisionReference
    right_reference: DecisionReference
    summary: str
    evidence_references: tuple[DecisionReference, ...] = ()
    scope: DecisionScope = DecisionScope()


@dataclass(frozen=True)
class RecommendationMetadata:
    recommendation_id: str
    summary: str
    decision_references: tuple[DecisionReference, ...] = ()
    alternative_references: tuple[DecisionReference, ...] = ()
    evidence_references: tuple[DecisionReference, ...] = ()
    governance_references: tuple[DecisionReference, ...] = ()
    confidence_reference: DecisionReference | None = None
    limitations: tuple[str, ...] = ()
    scope: DecisionScope = DecisionScope()

    @property
    def advisory(self) -> bool:
        return True

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class EvaluationMetadata:
    evaluation_id: str
    subject_reference: DecisionReference
    outcome: str = "not-evaluated"
    evidence_references: tuple[DecisionReference, ...] = ()
    scope: DecisionScope = DecisionScope()


@dataclass(frozen=True)
class ConfidenceMetadata:
    confidence_id: str
    value: float | None = None
    calibrated_value: float | None = None
    calibration_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )
    scope: DecisionScope = DecisionScope()

    def __post_init__(self) -> None:
        for name, value in (
            ("value", self.value),
            ("calibrated_value", self.calibrated_value),
        ):
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        object.__setattr__(
            self, "calibration_metadata", immutable_metadata(self.calibration_metadata)
        )


@dataclass(frozen=True)
class EvidenceMetadata:
    evidence_id: str
    source_reference: DecisionReference
    reliability: float | None = None
    scope: DecisionScope = DecisionScope()

    def __post_init__(self) -> None:
        if self.reliability is not None and not 0 <= self.reliability <= 1:
            raise ValueError("reliability must be between 0 and 1")


@dataclass(frozen=True)
class ReviewMetadata:
    review_id: str
    subject_reference: DecisionReference
    reviewer_references: tuple[DecisionReference, ...] = ()
    findings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    audit: tuple[Mapping[str, object], ...] = ()
    scope: DecisionScope = DecisionScope()


@dataclass(frozen=True)
class ApprovalMetadata:
    approval_id: str
    subject_reference: DecisionReference
    approver_references: tuple[DecisionReference, ...] = ()
    status: str = "not-reviewed"
    audit: tuple[Mapping[str, object], ...] = ()
    scope: DecisionScope = DecisionScope()

    @property
    def authorizes_execution(self) -> bool:
        return False


@dataclass(frozen=True)
class CompatibilityMetadata:
    compatibility_id: str
    source: DecisionReference
    target: DecisionReference
    status: str = "compatible"
    notes: tuple[str, ...] = ()
    scope: DecisionScope = DecisionScope()


Reference = DecisionReference

__all__ = (
    "AlternativeMetadata",
    "ApprovalMetadata",
    "ComparisonKind",
    "ComparisonMetadata",
    "CompatibilityMetadata",
    "ConfidenceMetadata",
    "DecisionLifecycle",
    "DecisionMetadata",
    "DecisionProfile",
    "DecisionReference",
    "DecisionScope",
    "EvaluationMetadata",
    "EvidenceMetadata",
    "RecommendationMetadata",
    "Reference",
    "ReviewMetadata",
    "immutable_metadata",
    "reject_executable_metadata",
)
