"""Composition root for the advisory V8 Hyper Reasoning Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_reasoning.contracts import (
    CompatibilityRecord,
    ConfidenceMetadata,
    EvaluationMetadata,
    EvidenceRecord,
    ExplanationSummary,
    KnowledgeReferenceRecord,
    ReasoningMetadata,
    ReasoningProfile,
    ReasoningReference,
    Recommendation,
)
from tkai.v8.hyper_reasoning.evidence import EvidenceAggregator
from tkai.v8.hyper_reasoning.registry import ReasoningRegistryCatalog
from tkai.v8.hyper_reasoning.security import secure_metadata
from tkai.v8.observability import Observability


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        filtered = secure_metadata(value)
        return {str(key): _serialize(item) for key, item in filtered.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def serialize_record(value: object) -> dict[str, object]:
    serialized = _serialize(value)
    if not isinstance(serialized, dict):
        raise TypeError("reasoning records must serialize to mappings")
    if isinstance(value, (ReasoningProfile, Recommendation)):
        serialized["execution_authorized"] = False
    if isinstance(value, Recommendation):
        serialized["advisory"] = True
    return serialized


class HyperReasoningFabric:
    """Metadata-driven reasoning coordination spanning V6, V7, and V8."""

    ID = "tkai-v8-hyper-reasoning"
    VERSION = "8.0.0"
    MODE = "reference-only"
    REGISTRY_NAMES = (
        "profiles",
        "reasoning",
        "evaluations",
        "confidence",
        "evidence",
        "knowledge",
        "recommendations",
        "explanations",
        "compatibility",
    )

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = ReasoningRegistryCatalog()
        self.aggregator = EvidenceAggregator()
        self.observability = Observability()
        self._sources: dict[str, tuple[ReasoningReference, ...]] = {
            name: () for name in EvidenceAggregator.SOURCE_NAMES
        }
        self.observability.audit("reasoning.initialized", "system", self.ID)

    def aggregate_evidence_metadata(
        self,
        *,
        v8_hyper_knowledge: tuple[
            ReasoningReference | Mapping[str, object], ...
        ] = (),
        v8_hyper_intelligence: tuple[
            ReasoningReference | Mapping[str, object], ...
        ] = (),
        v8_frameworks: tuple[ReasoningReference | Mapping[str, object], ...] = (),
        v7_frameworks: tuple[ReasoningReference | Mapping[str, object], ...] = (),
        v6_ai_centers: tuple[ReasoningReference | Mapping[str, object], ...] = (),
        actor: str = "system",
    ) -> dict[str, tuple[ReasoningReference, ...]]:
        self._sources = self.aggregator.aggregate(
            v8_hyper_knowledge=v8_hyper_knowledge,
            v8_hyper_intelligence=v8_hyper_intelligence,
            v8_frameworks=v8_frameworks,
            v7_frameworks=v7_frameworks,
            v6_ai_centers=v6_ai_centers,
        )
        count = sum(len(items) for items in self._sources.values())
        self.observability.increment("reasoning.evidence.references.aggregated", count)
        self.observability.audit(
            "reasoning.evidence.metadata.aggregated",
            actor,
            self.ID,
            {"references": count},
        )
        return dict(self._sources)

    aggregate_metadata = aggregate_evidence_metadata

    def _register(
        self, registry_name: str, value: object, identifier: str, actor: str
    ) -> object:
        registry = getattr(self.registries, registry_name)
        result = registry.register(value)
        self.observability.increment(f"reasoning.{registry_name}.registered")
        self.observability.audit(
            f"reasoning.{registry_name}.registered", actor, identifier
        )
        return result

    def register_profile(
        self, value: ReasoningProfile, actor: str = "system"
    ) -> ReasoningProfile:
        return self._register("profiles", value, value.profile_id, actor)  # type: ignore[return-value]

    def register_reasoning(
        self, value: ReasoningMetadata, actor: str = "system"
    ) -> ReasoningMetadata:
        return self._register("reasoning", value, value.reasoning_id, actor)  # type: ignore[return-value]

    def register_evaluation(
        self, value: EvaluationMetadata, actor: str = "system"
    ) -> EvaluationMetadata:
        return self._register("evaluations", value, value.evaluation_id, actor)  # type: ignore[return-value]

    def register_confidence(
        self, value: ConfidenceMetadata, actor: str = "system"
    ) -> ConfidenceMetadata:
        return self._register("confidence", value, value.confidence_id, actor)  # type: ignore[return-value]

    def register_evidence(
        self, value: EvidenceRecord, actor: str = "system"
    ) -> EvidenceRecord:
        return self._register("evidence", value, value.evidence_id, actor)  # type: ignore[return-value]

    def register_knowledge(
        self, value: KnowledgeReferenceRecord, actor: str = "system"
    ) -> KnowledgeReferenceRecord:
        return self._register("knowledge", value, value.knowledge_id, actor)  # type: ignore[return-value]

    def register_recommendation(
        self, value: Recommendation, actor: str = "system"
    ) -> Recommendation:
        return self._register(  # type: ignore[return-value]
            "recommendations", value, value.recommendation_id, actor
        )

    def register_explanation(
        self, value: ExplanationSummary, actor: str = "system"
    ) -> ExplanationSummary:
        return self._register("explanations", value, value.explanation_id, actor)  # type: ignore[return-value]

    def register_compatibility(
        self, value: CompatibilityRecord, actor: str = "system"
    ) -> CompatibilityRecord:
        return self._register(  # type: ignore[return-value]
            "compatibility", value, value.compatibility_id, actor
        )

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        evidence_ids = {
            item.evidence_id for item in self.registries.evidence.discover()
        }
        findings: list[dict[str, object]] = []
        for item in self.registries.reasoning.discover():
            for reference in item.evidence_references:
                if reference.identifier not in evidence_ids:
                    findings.append(
                        {
                            "code": "unresolved-evidence-reference",
                            "severity": "info",
                            "reasoning_id": item.reasoning_id,
                            "reference": reference.identifier,
                        }
                    )
        return tuple(findings)

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "mode": self.MODE,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "hidden_reasoning_storage": "prohibited",
            "chain_of_thought_retrieval": "prohibited",
            "sources": {
                source: len(references)
                for source, references in self._sources.items()
            },
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

    def overview(self) -> dict[str, object]:
        return {
            "fabric_id": self.ID,
            "version": self.VERSION,
            "mode": self.MODE,
            "metadata_only": True,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "hidden_reasoning_storage": "prohibited",
            "supported_generations": ("v6", "v7", "v8"),
            "metadata": dict(self.metadata),
            "health": self.health(),
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
            "overview": self.overview(),
            **records,
            "sources": {
                name: [_serialize(item) for item in items]
                for name, items in self._sources.items()
            },
            "health": self.health(),
            "metrics": self.metrics(),
            "diagnostics": self.diagnostics(),
            "logs": self.observability.logs(),
            "traces": [
                serialize_record(item) for item in self.observability.traces()
            ],
            "audit": self.observability.audit_records(),
        }

    @staticmethod
    def executes_tiktok_actions() -> bool:
        return False

    @staticmethod
    def mutates_runtime_state() -> bool:
        return False

    @staticmethod
    def exposes_chain_of_thought() -> bool:
        return False

    @staticmethod
    def authorizes_execution() -> bool:
        return False


ReasoningFabric = HyperReasoningFabric

__all__ = ("HyperReasoningFabric", "ReasoningFabric", "serialize_record")
