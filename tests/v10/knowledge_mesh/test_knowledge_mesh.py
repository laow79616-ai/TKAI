"""Offline mock-only tests for the V10 Sovereign Knowledge Mesh."""

from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.knowledge_mesh import (
    SUPPORTED_GENERATIONS,
    DomainRecord,
    EvidenceRecord,
    KnowledgeConcept,
    KnowledgeDomain,
    KnowledgeEntity,
    KnowledgeProfile,
    KnowledgeRelationship,
    LineageRecord,
    ProvenanceRecord,
    RelationshipType,
    SovereignKnowledgeMesh,
)
from tkai.v10.knowledge_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.knowledge_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.knowledge_mesh.security import authorize_metadata_read


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_structure_profile_domains_and_compatibility() -> None:
    root = Path(__file__).resolve().parents[3]
    required = set(
        """profiles registry domains concepts entities relationships references
        evidence provenance lineage versions taxonomy ontology classification catalog
        indexes search compatibility governance integrity trust validation diagnostics
        health metrics audit security events contracts interfaces lifecycle dashboard
        api""".split()
    )
    package = root / "src/tkai/v10/knowledge_mesh"
    assert required <= {item.name for item in package.iterdir() if item.is_dir()}
    mesh = SovereignKnowledgeMesh()
    profile = KnowledgeProfile("p", "v10:module", KnowledgeDomain.MODULE)
    mesh.register("profiles", profile)
    assert len(KnowledgeDomain) == 14
    assert {item.generation for item in mesh.discover("compatibility")} == set(
        SUPPORTED_GENERATIONS
    )


def test_concepts_entities_relationships_and_reference_only_domains() -> None:
    mesh = SovereignKnowledgeMesh()
    domain = DomainRecord("framework", KnowledgeDomain.FRAMEWORK, "Framework")
    concept = KnowledgeConcept(
        "concept",
        "Mesh",
        "Metadata mesh",
        "architecture",
        KnowledgeDomain.FRAMEWORK,
        tags=("local-first",),
    )
    entity = KnowledgeEntity("entity", "module", references=("v10:module",))
    mesh.register("domains", domain)
    mesh.register("concepts", concept)
    mesh.register("entities", entity)
    for kind in RelationshipType:
        relationship = KnowledgeRelationship(
            f"r-{kind.value}", "source", "target", kind
        )
        mesh.register("relationships", relationship)
        assert relationship.reference_only is True
    assert domain.reference_only is True and len(RelationshipType) == 8


def test_evidence_provenance_lineage_and_search_are_metadata_only() -> None:
    mesh = SovereignKnowledgeMesh()
    evidence = EvidenceRecord("e", "subject", "local:source", "local:evidence")
    provenance = ProvenanceRecord("p", "subject", "local:source", ("source", "subject"))
    lineage = LineageRecord("l", "subject", ("v6:x", "v10:x"))
    mesh.register("evidence", evidence)
    mesh.register("provenance", provenance)
    mesh.register("lineage", lineage)
    mesh.register(
        "concepts",
        KnowledgeConcept(
            "searchable",
            "Sovereignty",
            "Local knowledge",
            "governance",
            KnowledgeDomain.DOCUMENTATION,
        ),
    )
    assert all(item.metadata_only for item in (evidence, provenance, lineage))
    assert mesh.search("sovereignty")[0]["registry"] == "concepts"
    assert mesh.search("") == ()
    with pytest.raises(ValueError, match="between 0 and 100"):
        mesh.search("x", limit=101)


def test_security_observability_health_metrics_and_dashboard() -> None:
    mesh = SovereignKnowledgeMesh()
    mesh.register(
        "profiles",
        KnowledgeProfile(
            "p", "subject", KnowledgeDomain.MODULE, safe_metadata={"label": "safe"}
        ),
    )
    assert mesh.health()["status"] == "healthy"
    assert mesh.metrics()["v10_knowledge_mesh_profiles_total"] == 1
    assert mesh.audit() and mesh.traces() and mesh.structured_logs()
    assert mesh.diagnostics()["runtime_mutation"] is False
    snapshot = dashboard_snapshot(mesh)
    assert len(DASHBOARD_SECTIONS) == 11
    assert snapshot["read_only"] is True and snapshot["actions"] == ()
    scope = Scope("tenant", "workspace")
    authorize_metadata_read(scope, scope, role_references=("reader",))
    with pytest.raises(PermissionError):
        authorize_metadata_read(scope, scope)
    with pytest.raises(ValueError, match="secret-bearing"):
        mesh.register(
            "entities",
            KnowledgeEntity("bad", "module", attributes={"api_key": "secret"}),
        )
    assert mesh.serialize({"password": "secret"}) == {"password": "[REDACTED]"}


def test_api_openapi_and_server_integration_are_get_only() -> None:
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 10
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert all(
        set(operations) == {"get"}
        for operations in openapi_contract()["paths"].values()
    )
    source = (Path(__file__).resolve().parents[3] / "server/api/app.py").read_text()
    assert "register_v10_sovereign_knowledge_mesh_routes(app)" in source


def test_no_action_ingestion_learning_or_mutation_capabilities() -> None:
    mesh = SovereignKnowledgeMesh()
    assert mesh.overview()["execution"] == "disabled"
    assert not any(
        hasattr(mesh, name)
        for name in (
            "execute",
            "apply",
            "ingest",
            "scan",
            "crawl",
            "learn",
            "rewrite",
            "mutate",
            "publish",
            "deploy",
            "browser",
            "tiktok",
        )
    )
