"""Comprehensive offline contracts for the V9 Adaptive Reasoning Mesh."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tkai.v9.reasoning_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v9.reasoning_mesh.confidence import calibrate
from tkai.v9.reasoning_mesh.contracts import (
    Alternative,
    Assumption,
    Comparison,
    Constraint,
    Context,
    Evidence,
    Explanation,
    Hypothesis,
    Observation,
    Profile,
    ReasoningLifecycle,
    ReasoningScope,
    ReasoningSession,
    Recommendation,
    Reference,
    Source,
)
from tkai.v9.reasoning_mesh.dashboard import DASHBOARD_SECTIONS
from tkai.v9.reasoning_mesh.evaluations import EVALUATION_TYPES, evaluate
from tkai.v9.reasoning_mesh.fabric import AdaptiveReasoningMesh
from tkai.v9.reasoning_mesh.federation import ALLOWED_FRAMEWORKS, ReadOnlyFederation
from tkai.v9.reasoning_mesh.security import AccessController, Principal, secure_metadata

ROOT = Path(__file__).resolve().parents[3]
REF = Reference("artifact-1", framework="v9_adaptive_knowledge_mesh", generation="v9")
SCOPE = ReasoningScope(
    "tenant-a", "workspace-a", "namespace-a", "profile-a", "context-a"
)


def test_repository_path_and_package_structure() -> None:
    assert ROOT.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    package = ROOT / "src/tkai/v9/reasoning_mesh"
    required = {
        "profiles",
        "registry",
        "federation",
        "contexts",
        "sources",
        "knowledge",
        "evidence",
        "signals",
        "observations",
        "hypotheses",
        "assumptions",
        "constraints",
        "reasoning",
        "alternatives",
        "comparisons",
        "evaluations",
        "confidence",
        "recommendations",
        "explanations",
        "reviews",
        "governance",
        "policies",
        "versions",
        "compatibility",
        "history",
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
    assert required.issubset({item.name for item in package.iterdir() if item.is_dir()})
    assert all((package / name / "__init__.py").exists() for name in required)


def test_profile_is_immutable_and_approval_is_advisory() -> None:
    profile = Profile(
        "profile-a",
        "Reasoning",
        "bounded",
        "9.0.0",
        "owner",
        lifecycle=ReasoningLifecycle.APPROVED_REFERENCE,
        scope=SCOPE,
    )
    assert profile.execution_authorized is False
    with pytest.raises(FrozenInstanceError):
        profile.name = "changed"  # type: ignore[misc]


def test_federation_is_bounded_allowlisted_local_and_read_only() -> None:
    federation = ReadOnlyFederation(maximum_sources=1)
    assert federation.federate((REF,)) == (REF,)
    assert federation.mutates_upstream() is False
    assert "v9_adaptive_meta_kernel" in ALLOWED_FRAMEWORKS
    with pytest.raises(ValueError, match="bounded source"):
        federation.federate((REF, REF))
    with pytest.raises(ValueError, match="allowlisted"):
        federation.federate((Reference("bad", framework="unknown"),))
    with pytest.raises(ValueError, match="external network"):
        federation.federate(
            (Reference("remote", framework="v8_frameworks", metadata={"remote": True}),)
        )


def test_context_source_and_evidence_are_reference_only_and_bounded() -> None:
    context = Context("context-a", REF, "analysis", REF, scope=SCOPE)
    source = Source(
        "source-a", "framework", REF, reliability=0.8, freshness=0.7, scope=SCOPE
    )
    evidence = Evidence(
        "evidence-a",
        "observation",
        REF,
        REF,
        payload_reference=REF,
        payload_hash="sha256:abc",
        reliability=0.8,
        relevance=0.9,
        freshness=0.7,
        confidence=0.75,
        scope=SCOPE,
    )
    assert context.subject_reference == REF
    assert source.framework_reference == REF
    assert evidence.payload_reference == REF
    assert not hasattr(evidence, "payload")
    with pytest.raises(ValueError, match="between 0 and 1"):
        Source("bad", "framework", REF, reliability=2)


def test_observations_hypotheses_and_assumptions_are_clearly_labeled() -> None:
    observation = Observation("obs", REF, "A bounded observation", scope=SCOPE)
    hypothesis = Hypothesis(
        "hyp",
        "A possible explanation",
        REF,
        falsification_criteria=("counter evidence",),
        scope=SCOPE,
    )
    assumption = Assumption("assumption", "An explicit premise", scope=SCOPE)
    assert observation.classification == "observation"
    assert hypothesis.classification == "hypothesis"
    assert assumption.classification == "assumption"
    with pytest.raises(ValueError, match="distinguished"):
        Observation("bad", REF, "not a fact", classification="fact")
    with pytest.raises(ValueError, match="hypotheses"):
        Hypothesis("bad", "claim", REF, classification="fact")


def test_constraints_sessions_and_alternatives_are_safe() -> None:
    assert Constraint("pause", "pause").constraint_type == "pause"
    session = ReasoningSession(
        "session", REF, REF, safe_summary="Evidence is mixed", scope=SCOPE
    )
    alternative = Alternative(
        "alt", REF, "Review", "Request evidence", confidence=0.5, scope=SCOPE
    )
    assert session.safe_summary
    assert alternative.confidence == 0.5
    with pytest.raises(ValueError, match="hidden reasoning"):
        ReasoningSession("bad", REF, REF, safe_metadata={"chain_of_thought": "secret"})


def test_comparisons_reject_causal_claims() -> None:
    with pytest.raises(ValueError, match="causal"):
        Comparison(
            "comparison",
            "hypothesis_vs_hypothesis",
            REF,
            REF,
            "wins",
            causal_claim=True,
        )


def test_evaluations_are_explainable_and_not_arbitrary_code() -> None:
    result = evaluate(
        "eval",
        EVALUATION_TYPES[0],
        {"coverage": 0.8},
        {"coverage": 1.0},
        supporting_references=(REF,),
    )
    assert result.score == 0.8
    assert "weighted metadata score" in result.explanation_summary
    assert not hasattr(result, "code")
    with pytest.raises(ValueError, match="unsupported"):
        evaluate("bad", "arbitrary_python", {"x": 1.0}, {"x": 1.0})


def test_confidence_calibration_does_not_claim_certainty() -> None:
    values = {
        name: 0.7
        for name in (
            "evidence",
            "knowledge",
            "source",
            "freshness",
            "risk",
            "compatibility",
            "governance",
        )
    }
    record = calibrate("confidence", 0.8, values, historical_accuracy_reference=REF)
    assert 0 <= record.calibrated_confidence <= 1
    assert "no certainty claimed" in record.calibration_explanation


def test_recommendations_are_non_executable_and_explanations_are_safe() -> None:
    recommendation = Recommendation(
        "rec", "evidence_collection", "Collect more evidence", (REF,), 0.5
    )
    explanation = Explanation(
        "explain",
        "Evidence is incomplete",
        evidence_used=(REF,),
        limitations=("bounded data",),
    )
    assert recommendation.advisory is True
    assert recommendation.executable is False
    assert not hasattr(explanation, "chain_of_thought")
    with pytest.raises(ValueError, match="hidden reasoning"):
        Explanation(
            "bad", "summary", evaluation_breakdown={"hidden_reasoning": "private"}
        )


def test_registry_isolation_rbac_secret_filtering_and_bounded_results() -> None:
    mesh = AdaptiveReasoningMesh(metadata={"api_key": "secret", "safe": "yes"})
    profile = Profile("profile-a", "Reasoning", "bounded", "9", "owner", scope=SCOPE)
    mesh.register("profiles", profile)
    assert mesh.registries.profiles.discover(SCOPE) == (profile,)
    other = ReasoningScope("tenant-b", "workspace-a", "namespace-a")
    assert mesh.registries.profiles.discover(other) == ()
    controller = AccessController()
    controller.authorize(
        Principal("reader", tenant="tenant-a", workspace="workspace-a"),
        "reasoning:read",
        SCOPE,
    )
    with pytest.raises(PermissionError, match="tenant"):
        controller.authorize(Principal("reader"), "reasoning:read", SCOPE)
    assert "secret" not in repr(secure_metadata({"api_key": "secret"}))
    with pytest.raises(ValueError, match="result limit"):
        mesh.registries.profiles.discover(limit=1001)


def test_metrics_health_analytics_audit_and_compatibility() -> None:
    mesh = AdaptiveReasoningMesh()
    snapshot = mesh.snapshot()
    assert snapshot["health"]["readiness"] is True
    assert "v9_reasoning_mesh_profiles_total" in snapshot["metrics"]
    assert snapshot["compatibility"]["generations"] == ("v6", "v7", "v8", "v9")
    assert snapshot["compatibility"]["automatic_migration"] is False
    assert snapshot["audit"]
    assert mesh.executes_tiktok_actions() is False
    assert mesh.mutates_runtime_state() is False
    assert mesh.approves_execution() is False


class RouteRecorder:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.append((path, tuple(methods)))


def test_api_is_complete_get_only_and_has_no_dangerous_endpoints() -> None:
    recorder = RouteRecorder()
    register_routes(recorder)
    required = {
        f"/v9/reasoning/{name}"
        for name in (
            "profiles",
            "federation",
            "contexts",
            "sources",
            "knowledge",
            "evidence",
            "signals",
            "observations",
            "hypotheses",
            "assumptions",
            "constraints",
            "reasoning",
            "alternatives",
            "comparisons",
            "evaluations",
            "confidence",
            "recommendations",
            "explanations",
            "reviews",
            "governance",
            "policies",
            "versions",
            "compatibility",
            "history",
            "analytics",
            "diagnostics",
            "health",
            "metrics",
            "audit",
            "lifecycle",
        )
    }
    assert set(GET_ROUTES) == required
    assert all(methods == ("GET",) for _, methods in recorder.routes)
    paths = openapi_contract()["paths"]
    assert all(set(operation) == {"get"} for operation in paths.values())
    forbidden = (
        "execute",
        "decision",
        "mutate",
        "approve",
        "external-ai",
        "chain-of-thought",
        "hidden-reasoning",
        "scratchpad",
        "secret",
    )
    assert not any(word in path for path in GET_ROUTES for word in forbidden)


def test_dashboard_and_cross_mesh_integration_references() -> None:
    assert len(DASHBOARD_SECTIONS) == 31
    governance = AdaptiveReasoningMesh().governance()
    references = governance["integration_references"]
    assert "v9_adaptive_meta_kernel" in references
    assert "v9_adaptive_governance_mesh" in references
