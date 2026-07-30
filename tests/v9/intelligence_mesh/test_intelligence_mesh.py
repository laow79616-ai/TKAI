"""Offline, mock-only tests for the V9 Adaptive Intelligence Mesh."""

from pathlib import Path

import pytest

from tkai.v9.intelligence_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v9.intelligence_mesh.contracts import (
    CompatibilityRecord,
    ConfidenceRecord,
    EvidenceRecord,
    FederationProfile,
    IntelligenceReference,
    IntelligenceScope,
    KnowledgeRecord,
    ReasoningSummary,
    Recommendation,
    SignalRecord,
)
from tkai.v9.intelligence_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v9.intelligence_mesh.fabric import AdaptiveIntelligenceMesh
from tkai.v9.intelligence_mesh.security import (
    IntelligenceAccessController,
    IntelligencePrincipal,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def ref(identifier: str, generation: str = "v9") -> IntelligenceReference:
    return IntelligenceReference(identifier, "1.0.0", generation=generation)


def test_required_structure_and_profile_contract() -> None:
    root = Path(__file__).resolve().parents[3]
    required = {
        "profiles",
        "registry",
        "federation",
        "knowledge",
        "evidence",
        "signals",
        "contexts",
        "reasoning",
        "confidence",
        "recommendations",
        "explanations",
        "compatibility",
        "governance",
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
    package = root / "src/tkai/v9/intelligence_mesh"
    assert required <= {item.name for item in package.iterdir() if item.is_dir()}
    profile = FederationProfile(
        "mesh",
        "9.0.0",
        "platform",
        framework_references=(ref("framework"),),
        knowledge_references=(ref("knowledge"),),
        evidence_references=(ref("evidence"),),
        signal_references=(ref("signal"),),
        context_references=(ref("context"),),
        compatibility_references=(ref("compatibility"),),
        governance_references=(ref("governance"),),
        health="healthy",
        metrics={"coverage": 1},
        audit=({"event": "mock"},),
    )
    assert profile.execution_authorized is False


def test_federation_is_reference_only_across_all_versions() -> None:
    mesh = AdaptiveIntelligenceMesh()
    sources = mesh.aggregate_metadata(
        v6_ai_centers=({"identifier": "v6-center"},),
        v7_frameworks=({"identifier": "v7-framework"},),
        v8_frameworks=({"identifier": "v8-framework"},),
        v9_components=({"identifier": "v9-component"},),
    )
    assert {items[0].generation for items in sources.values()} == {
        "v6",
        "v7",
        "v8",
        "v9",
    }
    assert not mesh.executes_tiktok_actions() and not mesh.mutates_runtime_state()


def test_metadata_records_and_advisory_recommendations() -> None:
    mesh = AdaptiveIntelligenceMesh()
    mesh.register_evidence(
        EvidenceRecord(
            "e1",
            ref("mock-source"),
            provenance={"source": "mock"},
            reliability=0.9,
            freshness="current",
            integrity="verified",
        )
    )
    mesh.register_knowledge(
        KnowledgeRecord(
            "k1",
            "Mock knowledge",
            "reference",
            evidence_references=(ref("e1"),),
            version="2.0.0",
        )
    )
    mesh.register_signal(SignalRecord("s1", "mock", ref("mock-source")))
    mesh.register_confidence(
        ConfidenceRecord(
            "c1",
            0.8,
            calibration={"method": "mock"},
            evidence_coverage=1,
            reliability=0.9,
            limitations=("mock-only",),
            version_history=("1.0",),
        )
    )
    mesh.register_recommendation(
        Recommendation(
            "r1",
            "Review the referenced evidence.",
            (ref("e1"),),
            confidence=0.8,
        )
    )
    assert mesh.metrics()["confidence"] == 1
    assert mesh.snapshot()["recommendations"][0]["execution_authorized"] is False


def test_safe_reasoning_never_persists_chain_of_thought() -> None:
    with pytest.raises(ValueError, match="hidden reasoning"):
        ReasoningSummary("unsafe", "summary", metadata={"chain_of_thought": "x"})
    safe = ReasoningSummary(
        "safe",
        "Evidence supports the advisory result.",
        evidence_references=(ref("e1"),),
        confidence_references=(ref("c1"),),
        evaluation_references=(ref("evaluation"),),
    )
    assert safe.summary.startswith("Evidence")


def test_compatibility_security_health_dashboard_and_api() -> None:
    mesh = AdaptiveIntelligenceMesh(metadata={"api_key": "secret"})
    mesh.register_compatibility(
        CompatibilityRecord("compat", ref("v6-center", "v6"), ref("mesh", "v9"))
    )
    controller = IntelligenceAccessController()
    principal = IntelligencePrincipal("reader", tenant="a", workspace="w")
    controller.authorize(principal, "intelligence:read", IntelligenceScope("a", "w"))
    with pytest.raises(PermissionError, match="tenant isolation"):
        controller.authorize(
            principal, "intelligence:read", IntelligenceScope("b", "w")
        )
    assert mesh.metadata["api_key"] == "[REDACTED]"
    assert mesh.health()["execution"] == "disabled"
    assert dashboard_snapshot(mesh)["sections"] == DASHBOARD_SECTIONS
    app = FakeApp()
    register_routes(app, mesh)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert set(openapi_contract()["paths"]) == set(GET_ROUTES)  # type: ignore[arg-type]
    assert not any(
        word in route
        for route in GET_ROUTES
        for word in ("execute", "action", "chain-of-thought", "reasoning")
    )
