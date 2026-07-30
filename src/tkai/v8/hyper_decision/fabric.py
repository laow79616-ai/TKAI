"""Composition root for the advisory V8 Hyper Decision Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_decision.contracts import (
    AlternativeMetadata,
    ApprovalMetadata,
    ComparisonMetadata,
    CompatibilityMetadata,
    ConfidenceMetadata,
    DecisionMetadata,
    DecisionProfile,
    EvaluationMetadata,
    EvidenceMetadata,
    RecommendationMetadata,
    ReviewMetadata,
)
from tkai.v8.hyper_decision.registry import DecisionRegistryCatalog
from tkai.v8.hyper_decision.security import secure_metadata
from tkai.v8.observability import Observability


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {
            str(key): _serialize(item) for key, item in secure_metadata(value).items()
        }
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def serialize_record(value: object) -> dict[str, object]:
    serialized = _serialize(value)
    if not isinstance(serialized, dict):
        raise TypeError("decision records must serialize to mappings")
    if isinstance(value, (DecisionProfile, DecisionMetadata, RecommendationMetadata)):
        serialized["execution_authorized"] = False
    if isinstance(value, DecisionMetadata):
        serialized["executable"] = False
    if isinstance(value, RecommendationMetadata):
        serialized["advisory"] = True
    if isinstance(value, ApprovalMetadata):
        serialized["authorizes_execution"] = False
    return serialized


class HyperDecisionFabric:
    """Metadata-driven advisory decisions spanning V6, V7, and V8."""

    ID = "tkai-v8-hyper-decision"
    VERSION = "8.0.0"
    MODE = "reference-only"
    REGISTRY_NAMES = (
        "profiles",
        "decisions",
        "alternatives",
        "comparisons",
        "recommendations",
        "evaluations",
        "confidence",
        "evidence",
        "reviews",
        "approvals",
        "compatibility",
    )

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = DecisionRegistryCatalog()
        self.observability = Observability()
        self._sources: dict[str, tuple[Mapping[str, object], ...]] = {
            "v6_ai_centers": (),
            "v7_frameworks": (),
            "v8_frameworks": (),
        }
        self.observability.audit("decision.initialized", "system", self.ID)

    def aggregate_metadata(
        self,
        *,
        v6_ai_centers: tuple[Mapping[str, object], ...] = (),
        v7_frameworks: tuple[Mapping[str, object], ...] = (),
        v8_frameworks: tuple[Mapping[str, object], ...] = (),
        actor: str = "system",
    ) -> dict[str, tuple[Mapping[str, object], ...]]:
        self._sources = {
            "v6_ai_centers": tuple(secure_metadata(x) for x in v6_ai_centers),
            "v7_frameworks": tuple(secure_metadata(x) for x in v7_frameworks),
            "v8_frameworks": tuple(secure_metadata(x) for x in v8_frameworks),
        }
        count = sum(len(items) for items in self._sources.values())
        self.observability.increment("decision.references.aggregated", count)
        self.observability.audit(
            "decision.metadata.aggregated", actor, self.ID, {"references": count}
        )
        return dict(self._sources)

    def _register(
        self, name: str, value: object, identifier: str, actor: str
    ) -> object:
        result = getattr(self.registries, name).register(value)
        self.observability.increment(f"decision.{name}.registered")
        self.observability.audit(f"decision.{name}.registered", actor, identifier)
        return result

    def register_profile(
        self, value: DecisionProfile, actor: str = "system"
    ) -> DecisionProfile:
        return self._register("profiles", value, value.profile_id, actor)  # type: ignore[return-value]

    def register_decision(
        self, value: DecisionMetadata, actor: str = "system"
    ) -> DecisionMetadata:
        return self._register("decisions", value, value.decision_id, actor)  # type: ignore[return-value]

    def register_alternative(
        self, value: AlternativeMetadata, actor: str = "system"
    ) -> AlternativeMetadata:
        return self._register("alternatives", value, value.alternative_id, actor)  # type: ignore[return-value]

    def register_comparison(
        self, value: ComparisonMetadata, actor: str = "system"
    ) -> ComparisonMetadata:
        return self._register("comparisons", value, value.comparison_id, actor)  # type: ignore[return-value]

    def register_recommendation(
        self, value: RecommendationMetadata, actor: str = "system"
    ) -> RecommendationMetadata:
        return self._register("recommendations", value, value.recommendation_id, actor)  # type: ignore[return-value]

    def register_evaluation(
        self, value: EvaluationMetadata, actor: str = "system"
    ) -> EvaluationMetadata:
        return self._register("evaluations", value, value.evaluation_id, actor)  # type: ignore[return-value]

    def register_confidence(
        self, value: ConfidenceMetadata, actor: str = "system"
    ) -> ConfidenceMetadata:
        return self._register("confidence", value, value.confidence_id, actor)  # type: ignore[return-value]

    def register_evidence(
        self, value: EvidenceMetadata, actor: str = "system"
    ) -> EvidenceMetadata:
        return self._register("evidence", value, value.evidence_id, actor)  # type: ignore[return-value]

    def register_review(
        self, value: ReviewMetadata, actor: str = "system"
    ) -> ReviewMetadata:
        return self._register("reviews", value, value.review_id, actor)  # type: ignore[return-value]

    def register_approval(
        self, value: ApprovalMetadata, actor: str = "system"
    ) -> ApprovalMetadata:
        return self._register("approvals", value, value.approval_id, actor)  # type: ignore[return-value]

    def register_compatibility(
        self, value: CompatibilityMetadata, actor: str = "system"
    ) -> CompatibilityMetadata:
        return self._register("compatibility", value, value.compatibility_id, actor)  # type: ignore[return-value]

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        evidence_ids = {
            item.evidence_id for item in self.registries.evidence.discover()
        }
        return tuple(
            {
                "code": "unresolved-evidence-reference",
                "severity": "info",
                "decision_id": decision.decision_id,
                "reference": reference.identifier,
            }
            for decision in self.registries.decisions.discover()
            for reference in decision.evidence_references
            if reference.identifier not in evidence_ids
        )

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "mode": self.MODE,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "automatic_approval": "disabled",
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        return {
            **{
                name: len(getattr(self.registries, name))
                for name in self.REGISTRY_NAMES
            },
            "aggregated_references": sum(
                len(items) for items in self._sources.values()
            ),
            "counters": self.observability.metrics(),
        }

    def snapshot(self) -> dict[str, object]:
        records = {
            name: [
                serialize_record(item)
                for item in getattr(self.registries, name).discover()
            ]
            for name in self.REGISTRY_NAMES
        }
        return {
            "overview": {
                "fabric_id": self.ID,
                "version": self.VERSION,
                "mode": self.MODE,
                "metadata_only": True,
                "advisory": True,
                "execution": "disabled",
                "runtime_mutation": "disabled",
                "automatic_approval": "disabled",
                "supported_generations": ("v6", "v7", "v8"),
                "metadata": dict(self.metadata),
            },
            **records,
            "sources": {
                name: [_serialize(x) for x in items]
                for name, items in self._sources.items()
            },
            "health": self.health(),
            "metrics": self.metrics(),
            "diagnostics": self.diagnostics(),
            "logs": self.observability.logs(),
            "traces": [serialize_record(x) for x in self.observability.traces()],
            "audit": self.observability.audit_records(),
        }

    @staticmethod
    def executes_tiktok_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False

    @staticmethod
    def authorizes_execution() -> bool:
        return False

    @staticmethod
    def automatically_approves() -> bool:
        return False


DecisionFabric = HyperDecisionFabric
__all__ = ("DecisionFabric", "HyperDecisionFabric", "serialize_record")
