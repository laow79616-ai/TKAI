"""Offline mock-only tests for the V11 Autonomous Knowledge Graph."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from server.api.app import create_app
from tkai.v11.contracts import Scope
from tkai.v11.knowledge_graph import (
    AutonomousKnowledgeGraph,
    GraphEdge,
    GraphNode,
    GraphProfile,
    NodeKind,
    RelationshipKind,
)
from tkai.v11.knowledge_graph.api import (
    FORBIDDEN_METHODS,
    GET_ROUTES,
    openapi_contract,
    route_handlers,
    validate_forbidden_endpoints,
)
from tkai.v11.knowledge_graph.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)

ROOT = Path(__file__).resolve().parents[3]
PACKAGE_NAMES = {
    "profiles",
    "registry",
    "nodes",
    "edges",
    "relationships",
    "taxonomy",
    "ontology",
    "catalog",
    "contexts",
    "references",
    "provenance",
    "lineage",
    "dependencies",
    "compatibility",
    "governance",
    "trust",
    "integrity",
    "reasoning",
    "planning",
    "operations",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "security",
    "events",
    "dashboard",
    "api",
}


def test_repository_verification_and_package_structure() -> None:
    assert ROOT == Path(r"C:\Users\laow7\Documents\TKAI")
    package = ROOT / "src/tkai/v11/knowledge_graph"
    assert (ROOT / ".git").is_dir()
    assert PACKAGE_NAMES <= {item.name for item in package.iterdir() if item.is_dir()}


def test_graph_profile_is_complete_immutable_and_advisory() -> None:
    profile = GraphProfile()
    assert profile.graph_id == "tkai-v11-autonomous-knowledge-graph"
    assert profile.version == "11.0.0"
    assert profile.advisory and profile.deterministic and profile.read_only
    assert not profile.executable
    assert len(profile.node_registry) == 21
    assert len(profile.relationship_registry) == 10
    with pytest.raises(FrozenInstanceError):
        profile.version = "changed"  # type: ignore[misc]


def test_all_node_types_are_reference_only_and_deterministically_ordered() -> None:
    graph = AutonomousKnowledgeGraph()
    nodes = graph.nodes()["items"]
    assert isinstance(nodes, tuple)
    assert tuple(node.kind for node in nodes) == tuple(NodeKind)
    assert all(not node.executable for node in nodes)


def test_all_edge_relationships_are_supported_and_reference_only() -> None:
    graph = AutonomousKnowledgeGraph()
    edges = graph.edges()["items"]
    assert isinstance(edges, tuple)
    assert {edge.relationship for edge in edges} == set(RelationshipKind)
    assert all(not edge.executable for edge in edges)


def test_relationships_and_dependencies_are_metadata_only() -> None:
    graph = AutonomousKnowledgeGraph()
    assert graph.relationships()["reference_only"] is True
    dependencies = graph.dependencies()
    assert dependencies["reference_only"] is True
    assert dependencies["execution_order"] == ()


def test_taxonomy_and_ontology_disable_inference() -> None:
    graph = AutonomousKnowledgeGraph()
    assert len(graph.taxonomy()["node_classifications"]) == len(NodeKind)
    assert graph.ontology()["relationship_types"] == tuple(
        item.value for item in RelationshipKind
    )
    assert graph.ontology()["inference_enabled"] is False


def test_invalid_edges_and_duplicate_ids_are_rejected() -> None:
    node = GraphNode("node:one", NodeKind.MODULE, "One")
    with pytest.raises(ValueError, match="unknown edge endpoint"):
        AutonomousKnowledgeGraph(
            GraphProfile(
                nodes=(node,),
                edges=(
                    GraphEdge(
                        "edge:one",
                        "node:one",
                        "node:missing",
                        RelationshipKind.REFERENCES,
                    ),
                ),
            )
        )
    with pytest.raises(ValueError, match="duplicate node id"):
        AutonomousKnowledgeGraph(GraphProfile(nodes=(node, node), edges=()))


def test_scope_isolation_and_secret_metadata_are_enforced() -> None:
    with pytest.raises(PermissionError, match="tenant"):
        AutonomousKnowledgeGraph(
            GraphProfile(scope=Scope(tenant="tenant-a")),
            scope=Scope(tenant="tenant-b"),
        )
    with pytest.raises(ValueError, match="secret-bearing"):
        AutonomousKnowledgeGraph(GraphProfile(safe_metadata={"api_key": "no"}))


def test_dashboard_is_read_only_and_has_required_sections() -> None:
    snapshot = dashboard_snapshot(AutonomousKnowledgeGraph())
    assert len(DASHBOARD_SECTIONS) == 12
    assert snapshot["read_only"] is True
    assert snapshot["actions"] == ()
    assert snapshot["mutation_enabled"] is False


def test_api_has_exactly_thirteen_get_only_routes() -> None:
    assert len(GET_ROUTES) == 13
    assert set(route_handlers(AutonomousKnowledgeGraph())) == set(GET_ROUTES)
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    assert all(set(operations) == {"get"} for operations in paths.values())
    assert all(
        method not in operations
        for operations in paths.values()
        for method in FORBIDDEN_METHODS
    )


def test_forbidden_endpoint_validation() -> None:
    assert validate_forbidden_endpoints()


def test_validation_diagnostics_health_metrics_and_audit() -> None:
    graph = AutonomousKnowledgeGraph()
    assert graph.validation()["valid"] is True
    assert graph.diagnostics()["status"] == "clear"
    assert graph.health()["status"] == "healthy"
    assert graph.metrics()["v11_graph_nodes_total"] == 21
    assert graph.metrics()["v11_graph_mutations_total"] == 0
    assert graph.audit() == {"items": (), "append_enabled": False}


def test_projection_filters_secrets_and_contains_no_hidden_reasoning() -> None:
    graph = AutonomousKnowledgeGraph()
    result = graph.projection({"password": "value", "reasoning": "reference-only"})
    assert result == {"password": "[REDACTED]", "reasoning": "reference-only"}
    assert "hidden_reasoning" not in graph.overview()


def test_aggregate_openapi_adds_graph_without_mutating_legacy_routes() -> None:
    schema = create_app().openapi()
    assert set(GET_ROUTES) <= set(schema["paths"])
    assert all(set(schema["paths"][path]) == {"get"} for path in GET_ROUTES)
    assert "/v11/intelligence" in schema["paths"]
    assert "/v10/core" in schema["paths"]
    assert any(path.startswith("/v9/") for path in schema["paths"])
    assert any(path.startswith("/v8/") for path in schema["paths"])
    assert any(path.startswith("/v7/") for path in schema["paths"])


def test_graph_does_not_expose_mutation_or_execution_methods() -> None:
    forbidden = {
        "add",
        "remove",
        "update",
        "delete",
        "execute",
        "plan",
        "schedule",
        "deploy",
        "recover",
        "traverse",
        "optimize",
    }
    public = {
        name
        for name in dir(AutonomousKnowledgeGraph)
        if not name.startswith("_")
    }
    assert not forbidden & public
