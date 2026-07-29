"""Hyper Intelligence Fabric composition root."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_intelligence.aggregation import MetadataAggregator
from tkai.v8.hyper_intelligence.contracts import (
    CompatibilityRecord,
    EvidenceRecord,
    HyperIntelligenceProfile,
    IntelligenceReference,
    KnowledgeRecord,
    ReasoningSummary,
    Recommendation,
    SignalRecord,
)
from tkai.v8.hyper_intelligence.registry import IntelligenceRegistryCatalog
from tkai.v8.hyper_intelligence.relationships import Relationship, RelationshipGraph
from tkai.v8.hyper_intelligence.security import secure_metadata
from tkai.v8.observability import Observability


def _serialize(value: object) -> object:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            item.name: _serialize(getattr(value, item.name)) for item in fields(value)
        }
    if isinstance(value, Mapping):
        return {str(key): _serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_serialize(item) for item in value]
    if isinstance(value, Enum):
        return value.value
    return value


def serialize_record(value: object) -> dict[str, object]:
    serialized = _serialize(value)
    if not isinstance(serialized, dict):
        raise TypeError("intelligence records must serialize to mappings")
    if isinstance(value, (HyperIntelligenceProfile, Recommendation)):
        serialized["execution_authorized"] = False
    if isinstance(value, Recommendation):
        serialized["advisory"] = True
    return serialized


class HyperIntelligenceFabric:
    """Metadata-driven intelligence integration spanning V6, V7, and V8."""

    ID = "tkai-v8-hyper-intelligence"
    VERSION = "8.0.0"
    MODE = "reference-only"

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = IntelligenceRegistryCatalog()
        self.aggregator = MetadataAggregator()
        self.relationships = RelationshipGraph()
        self.observability = Observability()
        self._sources: dict[str, tuple[IntelligenceReference, ...]] = {
            "v6_ai_centers": (),
            "v7_frameworks": (),
            "v8_frameworks": (),
        }
        self.observability.audit("intelligence.initialized", "system", self.ID)

    def aggregate_metadata(
        self,
        *,
        v6_ai_centers: tuple[IntelligenceReference | Mapping[str, object], ...] = (),
        v7_frameworks: tuple[IntelligenceReference | Mapping[str, object], ...] = (),
        v8_frameworks: tuple[IntelligenceReference | Mapping[str, object], ...] = (),
        actor: str = "system",
    ) -> dict[str, tuple[IntelligenceReference, ...]]:
        """Replace the local reference projection; referenced runtimes are untouched."""

        self._sources = self.aggregator.aggregate_all(
            v6_ai_centers=v6_ai_centers,
            v7_frameworks=v7_frameworks,
            v8_frameworks=v8_frameworks,
        )
        count = sum(len(items) for items in self._sources.values())
        self.observability.increment("intelligence.references.aggregated", count)
        self.observability.audit(
            "intelligence.metadata.aggregated",
            actor,
            self.ID,
            {"references": count},
        )
        return dict(self._sources)

    def _audit_registration(
        self, registry_name: str, identifier: str, actor: str
    ) -> None:
        self.observability.increment(f"intelligence.{registry_name}.registered")
        self.observability.audit(
            f"intelligence.{registry_name}.registered", actor, identifier
        )

    def register_profile(
        self, value: HyperIntelligenceProfile, actor: str = "system"
    ) -> HyperIntelligenceProfile:
        registered = self.registries.profiles.register(value)
        self._audit_registration("profiles", value.profile_id, actor)
        return registered

    def register_knowledge(
        self, value: KnowledgeRecord, actor: str = "system"
    ) -> KnowledgeRecord:
        registered = self.registries.knowledge.register(value)
        self._audit_registration("knowledge", value.knowledge_id, actor)
        return registered

    def register_evidence(
        self, value: EvidenceRecord, actor: str = "system"
    ) -> EvidenceRecord:
        registered = self.registries.evidence.register(value)
        self._audit_registration("evidence", value.evidence_id, actor)
        return registered

    def register_signal(
        self, value: SignalRecord, actor: str = "system"
    ) -> SignalRecord:
        registered = self.registries.signals.register(value)
        self._audit_registration("signals", value.signal_id, actor)
        return registered

    def register_reasoning(
        self, value: ReasoningSummary, actor: str = "system"
    ) -> ReasoningSummary:
        registered = self.registries.reasoning.register(value)
        self._audit_registration("reasoning", value.summary_id, actor)
        return registered

    def register_recommendation(
        self, value: Recommendation, actor: str = "system"
    ) -> Recommendation:
        registered = self.registries.recommendations.register(value)
        self._audit_registration(
            "recommendations", value.recommendation_id, actor
        )
        return registered

    def register_compatibility(
        self, value: CompatibilityRecord, actor: str = "system"
    ) -> CompatibilityRecord:
        registered = self.registries.compatibility.register(value)
        self._audit_registration(
            "compatibility", value.compatibility_id, actor
        )
        return registered

    def add_relationship(
        self, value: Relationship, actor: str = "system"
    ) -> Relationship:
        added = self.relationships.add(value)
        self.observability.increment("intelligence.relationships.registered")
        self.observability.audit(
            "intelligence.relationship.registered",
            actor,
            f"{value.source}:{value.target}",
        )
        return added

    def health(self) -> dict[str, object]:
        return {
            "status": "healthy",
            "mode": self.MODE,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "sources": {
                generation: len(items)
                for generation, items in self._sources.items()
            },
            "diagnostics": self.diagnostics(),
        }

    def metrics(self) -> dict[str, object]:
        return {
            "profiles": len(self.registries.profiles),
            "knowledge": len(self.registries.knowledge),
            "evidence": len(self.registries.evidence),
            "signals": len(self.registries.signals),
            "reasoning_summaries": len(self.registries.reasoning),
            "recommendations": len(self.registries.recommendations),
            "compatibility": len(self.registries.compatibility),
            "relationships": len(self.relationships.relationships()),
            "aggregated_references": sum(
                len(items) for items in self._sources.values()
            ),
            "counters": self.observability.metrics(),
        }

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        missing_evidence: list[dict[str, object]] = []
        for item in self.registries.knowledge.discover():
            if item.evidence_references:
                continue
            missing_evidence.append(
                {
                "code": "knowledge-without-evidence",
                "severity": "info",
                "knowledge_id": item.knowledge_id,
                }
            )
        return tuple(missing_evidence)

    def overview(self) -> dict[str, object]:
        return {
            "fabric_id": self.ID,
            "version": self.VERSION,
            "mode": self.MODE,
            "metadata_only": True,
            "advisory": True,
            "execution": "disabled",
            "runtime_mutation": "disabled",
            "execution_approval": "disabled",
            "hidden_reasoning_storage": "prohibited",
            "supported_generations": ("v6", "v7", "v8"),
            "metadata": dict(self.metadata),
            "health": self.health(),
        }

    def snapshot(self) -> dict[str, object]:
        records = {
            name: [serialize_record(item) for item in registry.discover()]
            for name, registry in (
                ("profiles", self.registries.profiles),
                ("knowledge", self.registries.knowledge),
                ("evidence", self.registries.evidence),
                ("signals", self.registries.signals),
                ("reasoning", self.registries.reasoning),
                ("recommendations", self.registries.recommendations),
                ("compatibility", self.registries.compatibility),
            )
        }
        return {
            "overview": self.overview(),
            **records,
            "sources": {
                name: [_serialize(item) for item in items]
                for name, items in self._sources.items()
            },
            "relationships": [
                serialize_record(item) for item in self.relationships.relationships()
            ],
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
    def approves_execution() -> bool:
        return False


IntelligenceFabric = HyperIntelligenceFabric

__all__ = ("HyperIntelligenceFabric", "IntelligenceFabric", "serialize_record")
