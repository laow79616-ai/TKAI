"""Immutable, reference-only contracts for Hyper Reasoning."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

_FORBIDDEN_REASONING_KEYS = frozenset(
    {
        "chain_of_thought",
        "chain-of-thought",
        "hidden_reasoning",
        "internal_reasoning",
        "scratchpad",
        "reasoning_trace",
        "thoughts",
    }
)


def immutable_metadata(
    values: Mapping[str, object] | None = None,
) -> Mapping[str, object]:
    return MappingProxyType(dict(values or {}))


def reject_hidden_reasoning(values: Mapping[str, object]) -> None:
    """Reject metadata shaped like hidden reasoning at every nesting level."""

    for key, value in values.items():
        if str(key).lower() in _FORBIDDEN_REASONING_KEYS:
            raise ValueError("hidden reasoning and chain-of-thought are prohibited")
        if isinstance(value, Mapping):
            reject_hidden_reasoning(value)


class ReasoningLifecycle(str, Enum):
    DRAFT = "draft"
    REGISTERED = "registered"
    EVALUATED = "evaluated"
    REVIEWED = "reviewed"
    SUPERSEDED = "superseded"
    ARCHIVED = "archived"


@dataclass(frozen=True)
class ReasoningScope:
    tenant: str = "default"
    workspace: str = "default"
    reasoning_namespace: str = "default"


@dataclass(frozen=True)
class ReasoningReference:
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
        reject_hidden_reasoning(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class ReasoningProfile:
    profile_id: str
    version: str
    owner: str
    context_references: tuple[ReasoningReference, ...] = ()
    evidence_references: tuple[ReasoningReference, ...] = ()
    knowledge_references: tuple[ReasoningReference, ...] = ()
    reasoning_references: tuple[ReasoningReference, ...] = ()
    evaluation_references: tuple[ReasoningReference, ...] = ()
    recommendation_references: tuple[ReasoningReference, ...] = ()
    compatibility_references: tuple[ReasoningReference, ...] = ()
    governance_references: tuple[ReasoningReference, ...] = ()
    health: str = "unknown"
    metrics: Mapping[str, object] = field(default_factory=immutable_metadata)
    audit: tuple[Mapping[str, object], ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()
    lifecycle: ReasoningLifecycle = ReasoningLifecycle.DRAFT

    def __post_init__(self) -> None:
        if not self.profile_id or not self.version or not self.owner:
            raise ValueError("profile_id, version, and owner are required")
        reject_hidden_reasoning(self.metadata)
        object.__setattr__(self, "metrics", immutable_metadata(self.metrics))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))
        object.__setattr__(
            self, "audit", tuple(immutable_metadata(item) for item in self.audit)
        )

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class ReasoningMetadata:
    reasoning_id: str
    summary: str
    context_references: tuple[ReasoningReference, ...] = ()
    evidence_references: tuple[ReasoningReference, ...] = ()
    evaluation_references: tuple[ReasoningReference, ...] = ()
    confidence_reference: ReasoningReference | None = None
    assumption_references: tuple[ReasoningReference, ...] = ()
    limitation_references: tuple[ReasoningReference, ...] = ()
    decision_references: tuple[ReasoningReference, ...] = ()
    governance_references: tuple[ReasoningReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if not self.reasoning_id or not self.summary:
            raise ValueError("reasoning_id and safe summary are required")
        reject_hidden_reasoning(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class EvaluationMetadata:
    evaluation_id: str
    reasoning_reference: ReasoningReference
    evaluator_reference: ReasoningReference | None = None
    outcome: str = "not-evaluated"
    criteria_references: tuple[ReasoningReference, ...] = ()
    evidence_references: tuple[ReasoningReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if not self.evaluation_id:
            raise ValueError("evaluation_id is required")
        reject_hidden_reasoning(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class ConfidenceMetadata:
    confidence_id: str
    value: float | None = None
    calibration_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )
    evidence_coverage: float | None = None
    reliability_metadata: Mapping[str, object] = field(
        default_factory=immutable_metadata
    )
    limitations: tuple[str, ...] = ()
    version_history: tuple[Mapping[str, object], ...] = ()
    evidence_references: tuple[ReasoningReference, ...] = ()
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        for name, value in (
            ("value", self.value),
            ("evidence_coverage", self.evidence_coverage),
        ):
            if value is not None and not 0 <= value <= 1:
                raise ValueError(f"{name} must be between 0 and 1")
        object.__setattr__(
            self, "calibration_metadata", immutable_metadata(self.calibration_metadata)
        )
        object.__setattr__(
            self, "reliability_metadata", immutable_metadata(self.reliability_metadata)
        )
        object.__setattr__(
            self,
            "version_history",
            tuple(immutable_metadata(item) for item in self.version_history),
        )


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    source_reference: ReasoningReference
    subject_references: tuple[ReasoningReference, ...] = ()
    provenance: Mapping[str, object] = field(default_factory=immutable_metadata)
    reliability: float | None = None
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id is required")
        if self.reliability is not None and not 0 <= self.reliability <= 1:
            raise ValueError("reliability must be between 0 and 1")
        object.__setattr__(self, "provenance", immutable_metadata(self.provenance))
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class KnowledgeReferenceRecord:
    knowledge_id: str
    knowledge_reference: ReasoningReference
    evidence_references: tuple[ReasoningReference, ...] = ()
    scope: ReasoningScope = ReasoningScope()


@dataclass(frozen=True)
class Recommendation:
    recommendation_id: str
    summary: str
    reasoning_references: tuple[ReasoningReference, ...] = ()
    evidence_references: tuple[ReasoningReference, ...] = ()
    confidence_reference: ReasoningReference | None = None
    decision_references: tuple[ReasoningReference, ...] = ()
    governance_references: tuple[ReasoningReference, ...] = ()
    limitations: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if not self.recommendation_id or not self.summary:
            raise ValueError("recommendation_id and summary are required")
        reject_hidden_reasoning(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))

    @property
    def advisory(self) -> bool:
        return True

    @property
    def execution_authorized(self) -> bool:
        return False


@dataclass(frozen=True)
class ExplanationSummary:
    explanation_id: str
    summary: str
    evidence_references: tuple[ReasoningReference, ...] = ()
    assumption_references: tuple[ReasoningReference, ...] = ()
    limitation_summaries: tuple[str, ...] = ()
    policy_references: tuple[ReasoningReference, ...] = ()
    decision_references: tuple[ReasoningReference, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if not self.explanation_id or not self.summary:
            raise ValueError("explanation_id and safe summary are required")
        reject_hidden_reasoning(self.metadata)
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


@dataclass(frozen=True)
class CompatibilityRecord:
    compatibility_id: str
    source: ReasoningReference
    target: ReasoningReference
    status: str = "compatible"
    notes: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=immutable_metadata)
    scope: ReasoningScope = ReasoningScope()

    def __post_init__(self) -> None:
        if not self.compatibility_id:
            raise ValueError("compatibility_id is required")
        object.__setattr__(self, "metadata", immutable_metadata(self.metadata))


Reference = ReasoningReference

__all__ = (
    "CompatibilityRecord",
    "ConfidenceMetadata",
    "EvaluationMetadata",
    "EvidenceRecord",
    "ExplanationSummary",
    "KnowledgeReferenceRecord",
    "ReasoningLifecycle",
    "ReasoningMetadata",
    "ReasoningProfile",
    "ReasoningReference",
    "ReasoningScope",
    "Recommendation",
    "Reference",
    "immutable_metadata",
    "reject_hidden_reasoning",
)
