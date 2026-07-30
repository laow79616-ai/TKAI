"""Offline tests for the V9 Adaptive Knowledge Mesh."""

from pathlib import Path

import pytest

from tkai.v9.knowledge_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v9.knowledge_mesh.contracts import (
    FederationProfile,
    KnowledgeLifecycle,
    KnowledgeScope,
)
from tkai.v9.knowledge_mesh.dashboard import DASHBOARD_SECTIONS
from tkai.v9.knowledge_mesh.fabric import AdaptiveKnowledgeMesh
from tkai.v9.knowledge_mesh.models import Confidence, QualityScore
from tkai.v9.knowledge_mesh.normalization import normalize_name
from tkai.v9.knowledge_mesh.quality import evaluate_quality
from tkai.v9.knowledge_mesh.relationships import RelationshipGraph
from tkai.v9.knowledge_mesh.security import (
    KnowledgeAccessController,
    KnowledgePrincipal,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, str] = {}

    def add_api_route(
        self, path: str, _handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = methods[0]


def test_repository_and_required_structure() -> None:
    root = Path(__file__).resolve().parents[3]
    assert root.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    package = root / "src/tkai/v9/knowledge_mesh"
    required = {
        "profiles",
        "registry",
        "federation",
        "ontology",
        "taxonomy",
        "domains",
        "concepts",
        "entities",
        "relationships",
        "knowledge",
        "evidence",
        "provenance",
        "lineage",
        "semantics",
        "normalization",
        "quality",
        "confidence",
        "versions",
        "compatibility",
        "governance",
        "policies",
        "analytics",
        "diagnostics",
        "health",
        "metrics",
        "audit",
        "security",
        "events",
        "contracts",
        "interfaces",
        "lifecycle",
        "dashboard",
        "api",
    }
    assert required <= {item.name for item in package.iterdir() if item.is_dir()}


def test_lifecycle_federation_and_safety() -> None:
    assert KnowledgeLifecycle.APPROVED_REFERENCE.value == "approved_reference"
    profile = FederationProfile("p", "9.0.0", "owner")
    assert profile.execution_authorized is False
    mesh = AdaptiveKnowledgeMesh(metadata={"api_key": "secret"})
    sources = mesh.aggregate_metadata(
        v6_ai_centers=({"identifier": "v6"},),
        v7_frameworks=({"identifier": "v7"},),
        v8_frameworks=({"identifier": "v8"},),
        v9_components=({"identifier": "v9"},),
    )
    assert len(sources) == 4 and mesh.metadata["api_key"] == "[REDACTED]"
    assert not mesh.executes_tiktok_actions()
    assert not mesh.mutates_runtime_state()
    assert not mesh.approves_execution()


def test_bounded_deterministic_quality_and_confidence() -> None:
    mesh = AdaptiveKnowledgeMesh()
    with pytest.raises(ValueError, match="bounded source"):
        mesh.aggregate_metadata(
            v9_components=tuple(
                {"identifier": f"source-{index}"} for index in range(257)
            )
        )
    assert normalize_name("  Canonical   Name ") == "canonical name"
    score = evaluate_quality(
        {"integrity": 1.0, "freshness": 0.5},
        {"integrity": 3.0, "freshness": 1.0},
    )
    assert isinstance(score, QualityScore) and score.score == 0.875
    with pytest.raises(ValueError, match="confidence"):
        Confidence(*(1.1 for _ in range(9)), confidence_explanation="unsupported")
    assert RelationshipGraph.executable() is False


def test_isolation_get_only_api_dashboard_and_openapi() -> None:
    controller = KnowledgeAccessController()
    principal = KnowledgePrincipal("reader", tenant="a", workspace="w")
    controller.authorize(principal, "knowledge:read", KnowledgeScope("a", "w"))
    with pytest.raises(PermissionError, match="tenant isolation"):
        controller.authorize(principal, "knowledge:read", KnowledgeScope("b", "w"))
    app = FakeApp()
    register_routes(app)
    assert set(app.routes) == set(GET_ROUTES)
    assert set(app.routes.values()) == {"GET"}
    assert set(openapi_contract()["paths"]) == set(GET_ROUTES)  # type: ignore[arg-type]
    assert len(GET_ROUTES) == 25
    assert all(route.startswith("/v9/knowledge/") for route in GET_ROUTES)
    assert not any(
        forbidden in route
        for route in GET_ROUTES
        for forbidden in ("write", "mutate", "execute", "migrate", "approve", "secret")
    )
    assert "Lifecycle" in DASHBOARD_SECTIONS
