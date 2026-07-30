from dataclasses import FrozenInstanceError

import pytest

from tkai.v9.decision_mesh import (
    AdaptiveDecisionMesh,
    Alternative,
    Approval,
    Comparison,
    Compatibility,
    Confidence,
    Decision,
    DecisionScope,
    Evaluation,
    Profile,
    Recommendation,
    Reference,
    Review,
)
from tkai.v9.decision_mesh.api import GET_ROUTES, openapi_contract, route_handlers
from tkai.v9.decision_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v9.decision_mesh.security import authorize


def reference(identifier: str = "ref-1", framework: str = "v9_components") -> Reference:
    return Reference(identifier, generation="v9", framework=framework)


def test_profile_contains_required_metadata_and_is_immutable() -> None:
    profile = Profile("profile-1", "9.0.0", "owner", metadata={"safe": True})
    assert profile.execution_authorized is False
    assert profile.metadata["safe"] is True
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_registers_decision_resources_and_keeps_them_non_executable() -> None:
    mesh = AdaptiveDecisionMesh()
    decision = Decision("decision-1", "Prefer A", "strategic")
    recommendation = Recommendation("recommendation-1", "Review A")
    approval = Approval("approval-1", reference(), reference("reviewer"))
    for name, record in (
        ("decisions", decision), ("recommendations", recommendation),
        ("approvals", approval),
    ):
        mesh.register(name, record)
    snapshot = mesh.snapshot()
    assert snapshot["decisions"][0]["executable"] is False
    assert snapshot["recommendations"][0] == {
        **snapshot["recommendations"][0], "advisory": True, "executable": False
    }
    assert snapshot["approvals"][0]["authorizes_execution"] is False


def test_federation_is_bounded_allowlisted_and_reference_only() -> None:
    mesh = AdaptiveDecisionMesh(maximum_sources=1)
    assert mesh.federate((reference(),))[0].identifier == "ref-1"
    assert mesh.federation.mutates_upstream() is False
    with pytest.raises(ValueError, match="bounded"):
        mesh.federate((reference("one"), reference("two")))
    with pytest.raises(ValueError, match="allowlisted"):
        AdaptiveDecisionMesh().federate((reference(framework="unknown"),))


def test_decision_alternative_evaluation_review_and_compatibility() -> None:
    mesh = AdaptiveDecisionMesh()
    records = (
        (
            "alternatives",
            Alternative(
                "alt-1", reference(), "Alternative", ("Outcome",), ("Risk",)
            ),
        ),
        (
            "comparisons",
            Comparison(
                "cmp-1",
                "decision_vs_decision",
                reference(),
                reference("ref-2"),
                "Diff",
            ),
        ),
        ("evaluations", Evaluation("eval-1", reference(), 0.8, ("Sound",))),
        (
            "confidence",
            Confidence(
                "confidence-1",
                0.7,
                {"method": "historical"},
                (),
                ("Sparse history",),
            ),
        ),
        (
            "reviews",
            Review(
                "review-1",
                reference("reviewer"),
                reference(),
                ("Finding",),
                ("Recommendation",),
            ),
        ),
        ("compatibility", Compatibility("compat-1", "v6", reference())),
    )
    for name, record in records:
        mesh.register(name, record)
    assert all(mesh.snapshot()[name] for name, _ in records)
    assert mesh.analytics()["average_confidence"] == 0.7


@pytest.mark.parametrize(
    "comparison_type",
    (
        "decision_vs_decision",
        "alternative_vs_alternative",
        "historical",
        "confidence",
        "governance",
        "compatibility",
    ),
)
def test_all_comparison_modes(comparison_type: str) -> None:
    assert Comparison(
        "cmp", comparison_type, reference(), reference("right"), "summary"
    )


def test_security_enforces_rbac_tenant_workspace_and_decision_isolation() -> None:
    actual = DecisionScope("tenant-a", "workspace-a", "decision-a")
    assert authorize("read", actual, actual)
    assert authorize("review", actual, DecisionScope("tenant-a", "workspace-a"))
    assert not authorize("execute", actual, actual)
    assert not authorize("read", actual, DecisionScope("tenant-b", "workspace-a"))
    assert not authorize("read", actual, DecisionScope("tenant-a", "workspace-b"))


def test_secret_filtering_is_recursive() -> None:
    with pytest.raises(ValueError, match="secret"):
        Profile("p", "9", "owner", metadata={"nested": {"api_key": "no"}})


def test_health_metrics_dashboard_and_audit_are_read_only() -> None:
    mesh = AdaptiveDecisionMesh()
    assert mesh.health()["status"] == "healthy"
    assert mesh.metrics()["v9_decision_mesh_execution_total"] == 0
    dashboard = dashboard_snapshot(mesh)
    assert dashboard["sections"] == DASHBOARD_SECTIONS
    assert "Decision Mesh Overview" in DASHBOARD_SECTIONS
    assert dashboard["audit"]


def test_api_is_get_only_and_has_no_execution_or_automatic_approval_endpoint() -> None:
    mesh = AdaptiveDecisionMesh()
    required = {
        "/v9/decision/profiles", "/v9/decision/federation",
        "/v9/decision/decisions", "/v9/decision/alternatives",
        "/v9/decision/comparisons", "/v9/decision/recommendations",
        "/v9/decision/confidence", "/v9/decision/compatibility",
        "/v9/decision/health", "/v9/decision/metrics",
    }
    assert required <= set(GET_ROUTES)
    assert set(route_handlers(mesh)) == set(GET_ROUTES)
    paths = openapi_contract()["paths"]
    assert all(set(operation) == {"get"} for operation in paths.values())
    assert not any("execute" in path or "automatic-approval" in path for path in paths)
    assert not mesh.executes_tiktok_actions()
    assert not mesh.mutates_runtime_state()
    assert not mesh.approves_execution()
