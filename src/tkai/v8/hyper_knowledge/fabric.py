"""Composition root for the V8 Hyper Knowledge Fabric."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from enum import Enum

from tkai.v8.hyper_knowledge.contracts import (
    CompatibilityRecord,
    EvidenceRecord,
    KnowledgeEntity,
    KnowledgeProfile,
    KnowledgeReference,
    KnowledgeRelationship,
    LineageRecord,
    OntologyConcept,
)
from tkai.v8.hyper_knowledge.knowledge import KnowledgeAggregator
from tkai.v8.hyper_knowledge.registry import KnowledgeRegistryCatalog
from tkai.v8.hyper_knowledge.relationships import KnowledgeGraph
from tkai.v8.hyper_knowledge.security import secure_metadata
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
        raise TypeError("knowledge records must serialize to mappings")
    return serialized


class HyperKnowledgeFabric:
    """Unified, advisory knowledge metadata spanning V6, V7, and V8."""

    ID = "tkai-v8-hyper-knowledge"
    VERSION = "8.0.0"
    MODE = "reference-only"
    REGISTRY_NAMES = (
        "profiles",
        "ontology",
        "entities",
        "relationships",
        "evidence",
        "lineage",
        "compatibility",
    )

    def __init__(self, *, metadata: Mapping[str, object] | None = None) -> None:
        self.metadata = secure_metadata(metadata or {})
        self.registries = KnowledgeRegistryCatalog()
        self.aggregator = KnowledgeAggregator()
        self.graph = KnowledgeGraph()
        self.observability = Observability()
        self._sources: dict[str, tuple[KnowledgeReference, ...]] = {
            name: () for name in KnowledgeAggregator.SOURCE_NAMES
        }
        self.observability.audit("knowledge.initialized", "system", self.ID)

    def aggregate_metadata(
        self,
        *,
        v6_ai_centers: tuple[KnowledgeReference | Mapping[str, object], ...] = (),
        v7_frameworks: tuple[KnowledgeReference | Mapping[str, object], ...] = (),
        v8_frameworks: tuple[KnowledgeReference | Mapping[str, object], ...] = (),
        actor: str = "system",
    ) -> dict[str, tuple[KnowledgeReference, ...]]:
        self._sources = self.aggregator.aggregate(
            v6_ai_centers=v6_ai_centers,
            v7_frameworks=v7_frameworks,
            v8_frameworks=v8_frameworks,
        )
        count = sum(len(items) for items in self._sources.values())
        self.observability.increment("knowledge.references.aggregated", count)
        self.observability.audit(
            "knowledge.metadata.aggregated", actor, self.ID, {"references": count}
        )
        return dict(self._sources)

    def _register(
        self, registry_name: str, value: object, identifier: str, actor: str
    ) -> object:
        registry = getattr(self.registries, registry_name)
        result = registry.register(value)
        self.observability.increment(f"knowledge.{registry_name}.registered")
        self.observability.audit(
            f"knowledge.{registry_name}.registered", actor, identifier
        )
        return result

    def register_profile(
        self, value: KnowledgeProfile, actor: str = "system"
    ) -> KnowledgeProfile:
        return self._register("profiles", value, value.profile_id, actor)  # type: ignore[return-value]

    def register_concept(
        self, value: OntologyConcept, actor: str = "system"
    ) -> OntologyConcept:
        return self._register("ontology", value, value.concept_id, actor)  # type: ignore[return-value]

    def register_entity(
        self, value: KnowledgeEntity, actor: str = "system"
    ) -> KnowledgeEntity:
        return self._register("entities", value, value.entity_id, actor)  # type: ignore[return-value]

    def register_relationship(
        self, value: KnowledgeRelationship, actor: str = "system"
    ) -> KnowledgeRelationship:
        registered = self._register(
            "relationships", value, value.relationship_id, actor
        )
        self.graph.add(value)
        return registered  # type: ignore[return-value]

    def register_evidence(
        self, value: EvidenceRecord, actor: str = "system"
    ) -> EvidenceRecord:
        return self._register("evidence", value, value.evidence_id, actor)  # type: ignore[return-value]

    def register_lineage(
        self, value: LineageRecord, actor: str = "system"
    ) -> LineageRecord:
        return self._register("lineage", value, value.lineage_id, actor)  # type: ignore[return-value]

    def register_compatibility(
        self, value: CompatibilityRecord, actor: str = "system"
    ) -> CompatibilityRecord:
        return self._register(  # type: ignore[return-value]
            "compatibility", value, value.compatibility_id, actor
        )

    def diagnostics(self) -> tuple[dict[str, object], ...]:
        findings: list[dict[str, object]] = []
        evidence_ids = {
            item.evidence_reference.identifier
            for item in self.registries.evidence.discover()
        }
        for relationship in self.registries.relationships.discover():
            for reference in relationship.evidence_references:
                if reference.identifier not in evidence_ids:
                    findings.append(
                        {
                            "code": "unresolved-evidence-reference",
                            "severity": "info",
                            "relationship_id": relationship.relationship_id,
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
            "graph_processing": "disabled",
            "sensitive_payload_storage": "prohibited",
            "sources": {
                generation: len(items)
                for generation, items in self._sources.items()
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
            "graph_processing": "disabled",
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
    def executes_graph_processing() -> bool:
        return False

    @staticmethod
    def stores_sensitive_payloads() -> bool:
        return False


KnowledgeFabric = HyperKnowledgeFabric

__all__ = ("HyperKnowledgeFabric", "KnowledgeFabric", "serialize_record")
