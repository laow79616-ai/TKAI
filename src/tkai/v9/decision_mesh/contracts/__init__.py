"""Immutable, non-executable contracts for the V9 Adaptive Decision Mesh."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

SECRET_KEYS = frozenset(
    {"access_token", "api_key", "authorization", "cookie", "password", "secret"}
)


def safe_metadata(values: Mapping[str, object] | None = None) -> Mapping[str, object]:
    """Copy metadata into an immutable mapping and reject secret-bearing keys."""
    copied = dict(values or {})
    for key, value in copied.items():
        normalized = str(key).lower().replace("-", "_")
        if normalized in SECRET_KEYS or any(part in normalized for part in SECRET_KEYS):
            raise ValueError("secret-bearing metadata is prohibited")
        if isinstance(value, Mapping):
            safe_metadata(value)
    return MappingProxyType(copied)


class DecisionLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    UNDER_REVIEW = "under_review"
    REVIEWED = "reviewed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class DecisionScope:
    tenant: str = "default"
    workspace: str = "default"
    decision: str = "*"


@dataclass(frozen=True)
class Reference:
    identifier: str
    version: str = ""
    kind: str = "metadata"
    generation: str = ""
    framework: str = ""
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)

    def __post_init__(self) -> None:
        if not self.identifier or any(char.isspace() for char in self.identifier):
            raise ValueError("reference identifier must not be empty or contain spaces")
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))


@dataclass(frozen=True)
class Profile:
    profile_id: str
    version: str
    owner: str
    context_references: tuple[Reference, ...] = ()
    decision_references: tuple[Reference, ...] = ()
    alternative_references: tuple[Reference, ...] = ()
    evaluation_references: tuple[Reference, ...] = ()
    recommendation_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=safe_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    scope: DecisionScope = DecisionScope()

    def __post_init__(self) -> None:
        if not all((self.profile_id, self.version, self.owner)):
            raise ValueError("profile_id, version, and owner are required")
        object.__setattr__(self, "metrics", safe_metadata(self.metrics))
        object.__setattr__(self, "metadata", safe_metadata(self.metadata))
        object.__setattr__(self, "audit", tuple(safe_metadata(x) for x in self.audit))

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class Context:
    context_id: str
    summary: str
    evidence_references: tuple[Reference, ...] = ()
    constraint_references: tuple[Reference, ...] = ()
    version: str = "1.0.0"
    scope: DecisionScope = DecisionScope()


@dataclass(frozen=True)
class Decision:
    decision_id: str
    summary: str
    classification: str
    evidence_references: tuple[Reference, ...] = ()
    reasoning_references: tuple[Reference, ...] = ()
    recommendation_references: tuple[Reference, ...] = ()
    evaluation_references: tuple[Reference, ...] = ()
    confidence_references: tuple[Reference, ...] = ()
    governance_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    version_history: tuple[Reference, ...] = ()
    version: str = "1.0.0"
    lifecycle: DecisionLifecycle = DecisionLifecycle.DRAFT
    scope: DecisionScope = DecisionScope()

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Alternative:
    alternative_id: str
    decision_reference: Reference
    summary: str
    expected_outcomes: tuple[str, ...] = ()
    risk_summaries: tuple[str, ...] = ()
    constraint_references: tuple[Reference, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    compatibility_references: tuple[Reference, ...] = ()
    version: str = "1.0.0"
    scope: DecisionScope = DecisionScope()


COMPARISON_TYPES = frozenset(
    {
        "decision_vs_decision",
        "alternative_vs_alternative",
        "historical",
        "confidence",
        "governance",
        "compatibility",
    }
)


@dataclass(frozen=True)
class Comparison:
    comparison_id: str
    comparison_type: str
    left_reference: Reference
    right_reference: Reference
    summary: str
    version: str = "1.0.0"
    scope: DecisionScope = DecisionScope()

    def __post_init__(self) -> None:
        if self.comparison_type not in COMPARISON_TYPES:
            raise ValueError("unsupported comparison type")


@dataclass(frozen=True)
class Evaluation:
    evaluation_id: str
    subject_reference: Reference
    score: float
    findings: tuple[str, ...] = ()
    evidence_references: tuple[Reference, ...] = ()
    version: str = "1.0.0"
    scope: DecisionScope = DecisionScope()

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 1:
            raise ValueError("score must be between 0 and 1")


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    summary: str
    supporting_references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()
    version: str = "1.0.0"
    scope: DecisionScope = DecisionScope()

    @property
    def advisory(self) -> bool:
        return True

    @property
    def executable(self) -> bool:
        return False


@dataclass(frozen=True)
class Confidence:
    confidence_id: str
    value: float
    calibration_metadata: Mapping[str, object] = field(default_factory=safe_metadata)
    historical_accuracy_references: tuple[Reference, ...] = ()
    limitations: tuple[str, ...] = ()
    version: str = "1.0.0"
    scope: DecisionScope = DecisionScope()

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 1:
            raise ValueError("confidence must be between 0 and 1")
        object.__setattr__(
            self, "calibration_metadata", safe_metadata(self.calibration_metadata)
        )


@dataclass(frozen=True)
class Review:
    review_id: str
    reviewer_reference: Reference
    subject_reference: Reference
    findings: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    audit_reference: Reference | None = None
    status: str = "pending"
    scope: DecisionScope = DecisionScope()


@dataclass(frozen=True)
class Approval:
    approval_id: str
    subject_reference: Reference
    approver_reference: Reference
    status: str = "recorded"
    audit_reference: Reference | None = None
    scope: DecisionScope = DecisionScope()

    @property
    def authorizes_execution(self) -> bool:
        return False


@dataclass(frozen=True)
class Compatibility:
    compatibility_id: str
    generation: str
    subject_reference: Reference
    status: str = "compatible"
    notes: tuple[str, ...] = ()
    scope: DecisionScope = DecisionScope()

    def __post_init__(self) -> None:
        if self.generation.lower() not in {"v6", "v7", "v8", "v9"}:
            raise ValueError("compatibility generation must be V6, V7, V8, or V9")


DecisionMeshProfile = Profile
DecisionReference = Reference

__all__ = (
    "Approval",
    "Alternative",
    "COMPARISON_TYPES",
    "Comparison",
    "Compatibility",
    "Confidence",
    "Context",
    "Decision",
    "DecisionLifecycle",
    "DecisionMeshProfile",
    "DecisionReference",
    "DecisionScope",
    "Evaluation",
    "Profile",
    "Recommendation",
    "Reference",
    "Review",
    "safe_metadata",
)
