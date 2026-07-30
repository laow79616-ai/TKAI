"""Mock-only coverage for the V8 Hyper Knowledge Fabric."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_knowledge.analytics import coverage_summary
from tkai.v8.hyper_knowledge.api import (
    GET_ROUTES,
    openapi_contract,
    register_routes,
)
from tkai.v8.hyper_knowledge.contracts import (
    CompatibilityRecord,
    EvidenceRecord,
    KnowledgeEntity,
    KnowledgeProfile,
    KnowledgeReference,
    KnowledgeRelationship,
    KnowledgeScope,
    LineageRecord,
    OntologyConcept,
)
from tkai.v8.hyper_knowledge.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)
from tkai.v8.hyper_knowledge.fabric import HyperKnowledgeFabric
from tkai.v8.hyper_knowledge.relationships import KnowledgeGraph
from tkai.v8.hyper_knowledge.security import (
    KnowledgeAccessController,
    KnowledgePrincipal,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self,
        path: str,
        handler: object,
        *,
        methods: list[str],
        tags: list[str],
    ) -> None:
        assert tags == ["V8 Hyper Knowledge"]
        self.routes[path] = (methods[0], handler)


def reference(identifier: str, generation: str = "v8") -> KnowledgeReference:
    return KnowledgeReference(identifier, generation=generation)


def test_knowledge_profile_is_complete_immutable_and_reference_only() -> None:
    item = KnowledgeProfile(
        "profile-1",
        "8.0.0",
        "knowledge-team",
        framework_references=(reference("framework-1"),),
        knowledge_references=(reference("knowledge-1"),),
        ontology_references=(reference("concept-1"),),
        evidence_references=(reference("evidence-1"),),
        relationship_references=(reference("relationship-1"),),
        compatibility_references=(reference("compatibility-1"),),
        governance_references=(reference("governance-1"),),
        health="healthy",
        metrics={"coverage": 1.0},
        audit=({"action": "mock-review"},),
        metadata={"classification": "internal"},
    )
    fabric = HyperKnowledgeFabric()
    fabric.register_profile(item)
    assert fabric.snapshot()["profiles"][0]["owner"] == "knowledge-team"
    with pytest.raises(FrozenInstanceError):
        item.owner = "changed"  # type: ignore[misc]


def test_ontology_supports_required_metadata() -> None:
    concept = OntologyConcept(
        "concept-1",
        "Framework",
        categories=("architecture",),
        domains=("tkai",),
        relationship_types=("is-a",),
        constraints=("reference-only",),
        aliases=("framework-metadata",),
        parent_references=(reference("concept-root"),),
        version="8.0.0",
    )
    fabric = HyperKnowledgeFabric()
    fabric.register_concept(concept)
    serialized = fabric.snapshot()["ontology"][0]
    assert serialized["aliases"] == ["framework-metadata"]
    assert serialized["parent_references"][0]["identifier"] == "concept-root"


def test_reference_only_graph_entities_and_evidence_relationships() -> None:
    fabric = HyperKnowledgeFabric()
    fabric.register_entity(
        KnowledgeEntity(
            "entity-1",
            "framework",
            framework_references=(reference("v7-framework", "v7"),),
        )
    )
    fabric.register_relationship(
        KnowledgeRelationship(
            "relationship-1",
            reference("entity-1"),
            reference("entity-2"),
            "supported-by",
            evidence_references=(reference("evidence-ref"),),
        )
    )
    assert fabric.metrics()["entities"] == 1
    assert fabric.metrics()["relationships"] == 1
    assert KnowledgeGraph().executes_graph_processing() is False
    assert fabric.diagnostics()[0]["code"] == "unresolved-evidence-reference"


def test_evidence_provenance_contains_no_payload_and_validates_reliability() -> None:
    evidence = EvidenceRecord(
        "evidence-1",
        reference("evidence-ref"),
        reference("mock-source"),
        "mock-fixture",
        "2026-01-01T00:00:00Z",
        integrity="sha256:mock",
        reliability=0.95,
        freshness="current",
        audit=({"review": "passed"},),
        metadata={"api_token": "mock-secret", "description": "safe"},
    )
    fabric = HyperKnowledgeFabric(
        metadata={"password": "mock", "nested": {"token": "x"}}
    )
    fabric.register_evidence(evidence)
    assert fabric.metadata["password"] == "[REDACTED]"
    assert fabric.metadata["nested"] == {"token": "[REDACTED]"}
    serialized = fabric.snapshot()["evidence"][0]
    assert serialized["metadata"]["api_token"] == "[REDACTED]"
    assert "payload" not in serialized
    assert fabric.stores_sensitive_payloads() is False
    with pytest.raises(ValueError, match="reliability"):
        EvidenceRecord(
            "bad",
            reference("bad-ref"),
            reference("source"),
            "mock",
            "now",
            reliability=1.1,
        )


def test_lineage_ancestry_derivation_compatibility_and_evolution() -> None:
    lineage = LineageRecord(
        "lineage-1",
        reference("knowledge-v8"),
        ancestor_references=(reference("knowledge-v6", "v6"),),
        superseded_references=(reference("knowledge-v7", "v7"),),
        derived_references=(reference("derived-v8"),),
        compatibility_history=(reference("compat-history"),),
        evolution_metadata={"change": "normalized"},
    )
    fabric = HyperKnowledgeFabric()
    fabric.register_lineage(lineage)
    result = fabric.snapshot()["lineage"][0]
    assert result["ancestor_references"][0]["generation"] == "v6"
    assert result["evolution_metadata"]["change"] == "normalized"


def test_cross_version_aggregation_and_backward_compatibility() -> None:
    fabric = HyperKnowledgeFabric()
    sources = fabric.aggregate_metadata(
        v6_ai_centers=({"id": "v6-center"},),
        v7_frameworks=({"identifier": "v7-framework"},),
        v8_frameworks=(reference("v8-framework"),),
    )
    assert [items[0].generation for items in sources.values()] == ["v6", "v7", "v8"]
    fabric.register_compatibility(
        CompatibilityRecord(
            "compatibility-1",
            reference("v6-center", "v6"),
            reference("v8-framework", "v8"),
        )
    )
    from tkai.v7.intelligence_framework import IntelligenceFramework
    from tkai.v8.hyper_governance import HyperGovernanceFabric

    assert IntelligenceFramework is not None
    assert HyperGovernanceFabric().executes_tiktok_actions() is False


def test_security_isolation_rbac_health_metrics_and_observability() -> None:
    controller = KnowledgeAccessController()
    principal = KnowledgePrincipal(
        "reader", tenant="tenant-a", workspace="workspace-a", knowledge="domain-a"
    )
    scope = KnowledgeScope("tenant-a", "workspace-a", "domain-a")
    controller.authorize(principal, "knowledge:read", scope)
    for invalid in (
        KnowledgeScope("tenant-b", "workspace-a", "domain-a"),
        KnowledgeScope("tenant-a", "workspace-b", "domain-a"),
        KnowledgeScope("tenant-a", "workspace-a", "domain-b"),
    ):
        with pytest.raises(PermissionError):
            controller.authorize(principal, "knowledge:read", invalid)
    with pytest.raises(PermissionError):
        controller.authorize(principal, "knowledge:write", scope)
    fabric = HyperKnowledgeFabric()
    fabric.observability.log("info", "mock log", {"credential": "hidden"})
    fabric.observability.trace("knowledge-read", "mock-correlation")
    snapshot = fabric.snapshot()
    assert snapshot["logs"][0]["metadata"]["credential"] == "[REDACTED]"
    assert snapshot["traces"]
    assert snapshot["audit"]
    assert fabric.health()["status"] == "healthy"
    assert fabric.metrics()["profiles"] == 0
    assert coverage_summary(fabric)["reference_only"] is True


def test_dashboard_api_openapi_and_execution_guards() -> None:
    fabric = HyperKnowledgeFabric()
    dashboard = dashboard_snapshot(fabric)
    assert dashboard["read_only"] is True
    assert set(dashboard["sections"]) == set(DASHBOARD_SECTIONS)
    assert set(DASHBOARD_SECTIONS) == {
        "Knowledge Overview",
        "Ontology",
        "Knowledge Graph",
        "Entities",
        "Relationships",
        "Evidence",
        "Lineage",
        "Compatibility",
        "Health",
        "Metrics",
        "Audit",
    }
    app = FakeApp()
    register_routes(app, fabric)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    assert set(paths) == set(GET_ROUTES)
    assert all(set(operation) == {"get"} for operation in paths.values())
    assert fabric.executes_tiktok_actions() is False
    assert fabric.mutates_runtime_state() is False
    assert fabric.executes_graph_processing() is False
