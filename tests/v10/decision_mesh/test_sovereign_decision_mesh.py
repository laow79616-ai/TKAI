"""Offline mock-only tests for the V10 Sovereign Decision Mesh."""
# ruff: noqa: E501

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.decision_mesh import (
    CriterionType,
    DecisionConfidence,
    DecisionContext,
    DecisionOption,
    DecisionProfile,
    Dependency,
    Evaluation,
    EvaluationCriterion,
    Limitation,
    LimitationType,
    OptionStatus,
    Recommendation,
    RecommendationStatus,
    Risk,
    SovereignDecisionMesh,
    Tradeoff,
)
from tkai.v10.decision_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.decision_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.decision_mesh.security import authorize_metadata_read


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], **_: object
    ) -> None:
        self.routes[path] = (methods[0], handler)


def test_repository_structure_profiles_and_compatibility() -> None:
    root = Path(__file__).resolve().parents[3]
    assert root.resolve() == Path(r"C:\Users\laow7\Documents\TKAI").resolve()
    required = set(
        """profiles registry contexts options criteria evaluations tradeoffs risks dependencies
        recommendations confidence limitations governance compatibility integrity trust reasoning
        knowledge validation diagnostics health metrics audit security events contracts interfaces
        lifecycle dashboard api""".split()
    )
    package = root / "src/tkai/v10/decision_mesh"
    assert required <= {path.name for path in package.iterdir() if path.is_dir()}
    profile = DecisionProfile("profile", "subject", safe_metadata={"label": "safe"})
    with pytest.raises(FrozenInstanceError):
        profile.health = "bad"  # type: ignore[misc]
    mesh = SovereignDecisionMesh()
    mesh.register("profiles", profile)
    assert {item.generation for item in mesh.discover("compatibility")} == {
        "v6",
        "v7",
        "v8",
        "v9",
        "v10",
    }


def test_context_options_criteria_evaluations_and_tradeoffs() -> None:
    mesh = SovereignDecisionMesh()
    context = DecisionContext("context", "subject", "bounded", "tenant", "workspace")
    option = DecisionOption("option", "subject", "safe summary", OptionStatus.CANDIDATE)
    criterion = EvaluationCriterion("criterion", CriterionType.SECURITY)
    evaluation = Evaluation("evaluation", ("option",), ("criterion",), confidence=0.8)
    tradeoff = Tradeoff("tradeoff", benefit="compatibility", cost="complexity")
    risk = Risk("risk", "bounded risk")
    dependency = Dependency("dependency", "subject", "v10:sovereign-core")
    for registry, record in (
        ("contexts", context),
        ("options", option),
        ("criteria", criterion),
        ("evaluations", evaluation),
        ("tradeoffs", tradeoff),
        ("risks", risk),
        ("dependencies", dependency),
    ):
        mesh.register(registry, record)
    assert len(OptionStatus) == 6
    assert len(CriterionType) == 15
    assert option.metadata_only and evaluation.metadata_only


def test_recommendations_confidence_limitations_are_advisory_and_explainable() -> None:
    mesh = SovereignDecisionMesh()
    recommendation = Recommendation(
        "recommendation", ("option",), RecommendationStatus.REVIEW_REQUIRED
    )
    confidence = DecisionConfidence(
        "confidence", 0.6, "medium", "partial", "Inputs cited"
    )
    limitation = Limitation(
        "limitation", LimitationType.MANUAL_REVIEW_REQUIRED, "Human review required"
    )
    mesh.register("recommendations", recommendation)
    mesh.register("confidence", confidence)
    mesh.register("limitations", limitation)
    assert len(RecommendationStatus) == 4
    assert len(LimitationType) == 7
    assert recommendation.advisory_only and not recommendation.executable
    assert confidence.explainable_metadata_only


def test_bounds_rbac_tenant_isolation_secrets_and_hidden_reasoning() -> None:
    mesh = SovereignDecisionMesh(per_registry_limit=5)
    scope = Scope("tenant", "workspace")
    authorize_metadata_read(scope, scope, role_references=("reader",))
    with pytest.raises(PermissionError):
        authorize_metadata_read(scope, scope)
    with pytest.raises(ValueError, match="hidden"):
        mesh.register(
            "profiles",
            DecisionProfile(
                "bad", "subject", safe_metadata={"chain_of_thought": "secret"}
            ),
        )
    with pytest.raises(ValueError, match="between 0 and 1"):
        mesh.register(
            "confidence",
            DecisionConfidence("bad", 1.1, "invalid", "none", "invalid"),
        )
    assert mesh.serialize({"api_key": "secret"}) == {"api_key": "[REDACTED]"}
    with pytest.raises(ValueError, match="between 0 and 100"):
        mesh.discover("profiles", limit=101)


def test_health_metrics_dashboard_and_integrations() -> None:
    mesh = SovereignDecisionMesh()
    mesh.register("profiles", DecisionProfile("profile", "subject"))
    assert mesh.health()["readiness"]
    assert mesh.metrics()["v10_decision_profiles_total"] == 1
    assert len(mesh.metrics()) == 10
    snapshot = dashboard_snapshot(mesh)
    assert len(DASHBOARD_SECTIONS) == 12
    assert snapshot["actions"] == ()
    assert len(mesh.overview()["integrations"]) == 7


def test_api_openapi_get_only_and_server_registration() -> None:
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 11
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert all(
        set(operations) == {"get"}
        for operations in openapi_contract()["paths"].values()
    )
    assert set(GET_ROUTES) == {
        f"/v10/decision/{name}"
        for name in (
            "profiles",
            "contexts",
            "options",
            "evaluations",
            "criteria",
            "tradeoffs",
            "recommendations",
            "confidence",
            "validation",
            "health",
            "metrics",
        )
    }
    root = Path(__file__).resolve().parents[3]
    assert (
        "register_v10_sovereign_decision_mesh_routes(app)"
        in (root / "server/api/app.py").read_text()
    )


def test_no_execution_write_planning_approval_or_hidden_reasoning_endpoints() -> None:
    mesh = SovereignDecisionMesh()
    forbidden = (
        "execute",
        "apply",
        "plan",
        "approve",
        "mutate",
        "write",
        "create",
        "update",
        "delete",
        "post",
        "put",
        "patch",
        "deploy",
        "chain-of-thought",
        "scratchpad",
        "hidden-prompt",
    )
    assert not any(any(term in path for term in forbidden) for path in GET_ROUTES)
    assert all(value is False for value in mesh.diagnostics().values())
    assert mesh.overview()["execution"] == "disabled"
    assert not any(
        hasattr(mesh, name)
        for name in (
            "execute",
            "apply",
            "plan",
            "approve",
            "mutate",
            "deploy",
            "start",
            "stop",
            "restart",
            "rollback",
        )
    )
