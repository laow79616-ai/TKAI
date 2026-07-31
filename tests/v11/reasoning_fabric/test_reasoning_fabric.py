"""Offline mock-only validation of the V11 Autonomous Reasoning Fabric."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from server.api.app import create_app
from tkai.v11.contracts import Scope
from tkai.v11.reasoning_fabric import (
    EVIDENCE_PROVIDERS,
    Alternative,
    AutonomousReasoningFabric,
    Claim,
    ClaimType,
    Confidence,
    EvidenceReference,
    FabricLimits,
    InferenceReference,
    InferenceType,
    ReasoningContext,
    ReasoningFabricProfile,
    SafeExplanation,
    UncertaintyStatus,
)
from tkai.v11.reasoning_fabric.api import (
    FORBIDDEN_METHODS,
    GET_ROUTES,
    openapi_contract,
    route_handlers,
    validate_forbidden_endpoints,
)
from tkai.v11.reasoning_fabric.dashboard import (
    DASHBOARD_SECTIONS,
    dashboard_snapshot,
)

ROOT = Path(__file__).resolve().parents[3]
PACKAGES = {
    "profiles",
    "registry",
    "contexts",
    "claims",
    "premises",
    "evidence",
    "inferences",
    "assumptions",
    "constraints",
    "alternatives",
    "contradictions",
    "confidence",
    "uncertainty",
    "explanations",
    "evaluations",
    "relationships",
    "knowledge_graph",
    "compatibility",
    "governance",
    "trust",
    "integrity",
    "validation",
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


def test_repository_path_and_package_structure() -> None:
    assert ROOT == Path(r"C:\Users\laow7\Documents\TKAI")
    package = ROOT / "src/tkai/v11/reasoning_fabric"
    assert (ROOT / ".git").is_dir()
    assert PACKAGES <= {item.name for item in package.iterdir() if item.is_dir()}


def test_profile_is_complete_immutable_bounded_and_advisory() -> None:
    profile = ReasoningFabricProfile()
    assert profile.fabric_profile_id == "tkai-v11-autonomous-reasoning-fabric"
    assert profile.compatibility_references == ("v6", "v7", "v8", "v9", "v10", "v11")
    assert profile.advisory and profile.deterministic and profile.read_only
    assert not profile.executable
    with pytest.raises(FrozenInstanceError):
        profile.version = "changed"  # type: ignore[misc]


def test_claim_and_inference_classifications_are_metadata_only() -> None:
    assert len(ClaimType) == 15
    assert len(InferenceType) == 12
    inference = InferenceReference(
        "inference:1", InferenceType.DEDUCTIVE_REFERENCE, "claim:1"
    )
    assert not inference.executable


def test_context_claim_evidence_and_knowledge_graph_references() -> None:
    context = ReasoningContext(
        "context:1",
        "subject:1",
        "bounded",
        knowledge_graph_references=("node:1",),
    )
    evidence = EvidenceReference(
        "evidence:1", "v11-autonomous-knowledge-graph", "node:1"
    )
    claim = Claim(
        "claim:1",
        ClaimType.OBSERVATIONAL,
        "subject:1",
        "Safe summary",
        evidence_references=("evidence:1",),
    )
    fabric = AutonomousReasoningFabric(
        ReasoningFabricProfile(
            contexts=(context,), claims=(claim,), evidence=(evidence,)
        )
    )
    assert fabric.contexts()["count"] == 1
    assert fabric.claims()["count"] == 1
    assert fabric.knowledge_graph()["graph_mutation"] is False
    assert fabric.knowledge_graph()["graph_execution"] is False


def test_evidence_provider_allowlist_and_no_automatic_ingestion() -> None:
    assert "v6-metadata-providers" in EVIDENCE_PROVIDERS
    with pytest.raises(ValueError, match="not allowlisted"):
        AutonomousReasoningFabric(
            ReasoningFabricProfile(
                evidence=(EvidenceReference("e:1", "external-search", "internet"),)
            )
        )


def test_bounded_collections_duplicate_ids_and_confidence_validation() -> None:
    context = ReasoningContext("same", "subject", "scope")
    with pytest.raises(ValueError, match="bounded limit"):
        AutonomousReasoningFabric(
            ReasoningFabricProfile(
                contexts=(context, context), limits=FabricLimits(contexts=1)
            )
        )
    with pytest.raises(ValueError, match="duplicate metadata id"):
        AutonomousReasoningFabric(
            ReasoningFabricProfile(
                claims=(
                    Claim("same", ClaimType.RISK, "s", "one"),
                    Claim("same", ClaimType.HEALTH, "s", "two"),
                )
            )
        )
    with pytest.raises(ValueError, match="invalid confidence"):
        AutonomousReasoningFabric(
            ReasoningFabricProfile(confidence=(Confidence("c:1", "high", 1.2),))
        )


def test_scope_isolation_and_safe_metadata_validation() -> None:
    with pytest.raises(PermissionError, match="tenant"):
        AutonomousReasoningFabric(
            ReasoningFabricProfile(scope=Scope(tenant="a")),
            scope=Scope(tenant="b"),
        )
    with pytest.raises(ValueError, match="secret-bearing"):
        AutonomousReasoningFabric(
            ReasoningFabricProfile(safe_metadata={"api_key": "secret"})
        )


def test_alternatives_are_not_selected_and_explanations_are_safe_summaries() -> None:
    alternative = Alternative("a:1", "Reference option")
    explanation = SafeExplanation("x:1", "User-facing evidence summary")
    fabric = AutonomousReasoningFabric(
        ReasoningFabricProfile(alternatives=(alternative,), explanations=(explanation,))
    )
    assert not alternative.automatically_selected
    projection = fabric.projection(
        {"password": "secret", "summary": explanation.summary}
    )
    assert projection == {
        "password": "[REDACTED]",
        "summary": "User-facing evidence summary",
    }


def test_uncertainty_registry_is_complete() -> None:
    assert {item.value for item in UncertaintyStatus} == {
        "known",
        "partially-known",
        "unknown",
        "conflicting",
        "insufficient-evidence",
        "outdated-reference",
        "unverified-reference",
        "unsupported",
        "manual-review-required",
    }


def test_validation_health_metrics_audit_and_lifecycle_are_read_only() -> None:
    fabric = AutonomousReasoningFabric()
    assert fabric.validation()["valid"] is True
    assert fabric.diagnostics()["status"] == "clear"
    assert fabric.health()["reasoning_readiness"] is True
    assert fabric.metrics()["v11_reasoning_fabric_profiles_total"] == 1
    assert fabric.audit()["append_enabled"] is False
    assert fabric.lifecycle()["mutation_enabled"] is False


def test_dashboard_has_all_read_only_projections() -> None:
    snapshot = dashboard_snapshot(AutonomousReasoningFabric())
    assert len(DASHBOARD_SECTIONS) == 27
    assert snapshot["read_only"] is True
    assert snapshot["actions"] == ()
    assert snapshot["mutation_enabled"] is False


def test_api_has_twenty_seven_get_only_routes_and_no_forbidden_endpoint() -> None:
    assert len(GET_ROUTES) == 27
    assert set(route_handlers(AutonomousReasoningFabric())) == set(GET_ROUTES)
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    assert all(set(operations) == {"get"} for operations in paths.values())
    assert all(
        method not in operations
        for operations in paths.values()
        for method in FORBIDDEN_METHODS
    )
    assert validate_forbidden_endpoints()


def test_aggregate_openapi_integrates_all_reasoning_routes() -> None:
    schema = create_app().openapi()
    assert set(GET_ROUTES) <= set(schema["paths"])
    assert all(set(schema["paths"][path]) == {"get"} for path in GET_ROUTES)
    assert "/v11/graph" in schema["paths"]
    assert "/v11/intelligence" in schema["paths"]
    assert "/v10/core" in schema["paths"]
    assert any(path.startswith("/v9/") for path in schema["paths"])
    assert any(path.startswith("/v8/") for path in schema["paths"])
    assert any(path.startswith("/v7/") for path in schema["paths"])


def test_no_hidden_reasoning_or_execution_surface() -> None:
    overview = AutonomousReasoningFabric().overview()
    assert overview["hidden_reasoning_storage"] is False
    assert overview["private_scratchpad_storage"] is False
    forbidden = {
        "execute",
        "decide",
        "plan",
        "approve",
        "migrate",
        "upgrade",
        "rollback",
        "mutate",
        "apply",
        "schedule",
        "allocate",
        "start",
        "stop",
        "restart",
        "deploy",
        "recover",
        "browse",
        "publish",
        "ingest",
    }
    public = {
        name for name in dir(AutonomousReasoningFabric) if not name.startswith("_")
    }
    assert not forbidden & public
