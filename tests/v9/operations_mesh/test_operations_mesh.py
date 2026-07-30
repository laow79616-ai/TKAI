from dataclasses import FrozenInstanceError

import pytest

from tkai.v9.operations_mesh import (
    AdaptiveOperationsMesh,
    Approval,
    Assessment,
    CapacityAssessment,
    Dependency,
    OperationReference,
    OperationsLifecycle,
    OperationsScope,
    Profile,
    Recommendation,
    Reference,
)
from tkai.v9.operations_mesh.api import GET_ROUTES, openapi_contract, route_handlers
from tkai.v9.operations_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v9.operations_mesh.security import authorize


def ref(identifier: str = "ref-1", framework: str = "v9_components") -> Reference:
    return Reference(identifier, generation="v9", framework=framework)


def scope() -> OperationsScope:
    return OperationsScope("tenant-a", "workspace-a", "namespace-a", "profile-a")


def test_profile_lifecycle_immutable_and_non_executable() -> None:
    profile = Profile(
        "p",
        "Profile",
        "desc",
        "9.0.0",
        "owner",
        "namespace-a",
        ref("tenant"),
        ref("workspace"),
        scope=scope(),
        lifecycle=OperationsLifecycle.APPROVED_REFERENCE,
    )
    assert profile.execution_authorized is False
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]
    assert {item.value for item in OperationsLifecycle} >= {
        "approved_reference",
        "degraded_reference",
        "deleted",
    }


def test_federation_is_bounded_local_allowlisted_and_read_only() -> None:
    mesh = AdaptiveOperationsMesh(maximum_sources=1)
    assert mesh.federate((ref(),))[0].identifier == "ref-1"
    assert not mesh.federation.mutates_upstream()
    with pytest.raises(ValueError, match="bounded"):
        mesh.federate((ref("a"), ref("b")))
    with pytest.raises(ValueError, match="allowlisted"):
        AdaptiveOperationsMesh().federate((ref(framework="unknown"),))
    with pytest.raises(ValueError, match="network"):
        AdaptiveOperationsMesh().federate(
            (Reference("remote", framework="v8_frameworks", metadata={"remote": True}),)
        )


def test_operations_assessments_capacity_and_approvals_are_advisory() -> None:
    mesh = AdaptiveOperationsMesh()
    operation = OperationReference("op-1", "workflow", ref("subject"), scope=scope())
    assessment = Assessment(
        "a-1",
        "workflow_readiness",
        0.8,
        "ready",
        {"evidence": 0.8},
        {"evidence": 1.0},
        explanation_summary="Evidence supports advisory readiness.",
        scope=scope(),
    )
    capacity = CapacityAssessment(
        "c-1",
        "worker",
        10,
        12,
        1.2,
        2,
        0,
        confidence=0.7,
        limitations=("estimate only",),
        scope=scope(),
    )
    approval = Approval(
        "approval-1",
        ref("artifact"),
        "1",
        "reference",
        "reviewer",
        "approved",
        scope=scope(),
    )
    recommendation = Recommendation(
        "r-1",
        "resource_planning",
        ref("artifact"),
        limitations=("manual review",),
        scope=scope(),
    )
    for name, value in (
        ("operations", operation),
        ("readiness", assessment),
        ("capacity", capacity),
        ("approvals", approval),
        ("recommendations", recommendation),
    ):
        mesh.register(name, value)
    snapshot = mesh.snapshot()
    assert snapshot["operations"][0]["executable"] is False
    assert snapshot["approvals"][0]["authorizes_execution"] is False
    assert snapshot["recommendations"][0]["executable"] is False
    assert capacity.allocates_resources is False
    assert mesh.analytics()["capacity_shortfalls_total"] == 1


def test_explainable_scores_reject_arbitrary_or_unbounded_values() -> None:
    with pytest.raises(ValueError, match="explainable"):
        Assessment("a", "runtime", 0.5, "unknown", {}, {}, explanation_summary="")
    with pytest.raises(ValueError, match="between"):
        Assessment(
            "a", "runtime", 2, "ready", {"x": 1}, {"x": 1}, explanation_summary="bad"
        )


def test_dependency_diagnostics_detect_missing_and_circular_dependencies() -> None:
    mesh = AdaptiveOperationsMesh()
    mesh.register(
        "dependencies",
        Dependency("d-a", "service", ref("a"), (ref("b"),), scope=scope()),
    )
    mesh.register(
        "dependencies",
        Dependency(
            "d-b", "service", ref("b"), (ref("a"), ref("missing")), scope=scope()
        ),
    )
    kinds = {item["type"] for item in mesh.dependency_issues()}
    assert kinds == {"missing_dependency", "circular_dependency"}


def test_security_isolation_secret_filtering_and_bounds() -> None:
    actual = scope()
    assert authorize("read", actual, actual)
    assert not authorize("execute", actual, actual)
    assert not authorize(
        "read",
        actual,
        OperationsScope("other", "workspace-a", "namespace-a", "profile-a"),
    )
    with pytest.raises(ValueError, match="secret"):
        AdaptiveOperationsMesh(metadata={"nested": {"api_key": "no"}})
    mesh = AdaptiveOperationsMesh(maximum_records=1)
    mesh.register(
        "operations", OperationReference("one", "reference", ref(), scope=scope())
    )
    with pytest.raises(ValueError, match="bounded"):
        mesh.register(
            "operations", OperationReference("two", "reference", ref(), scope=scope())
        )


def test_health_metrics_dashboard_and_get_only_api() -> None:
    mesh = AdaptiveOperationsMesh()
    assert mesh.health()["status"] == "healthy"
    required_metrics = {
        "v9_operations_mesh_profiles_total",
        "v9_operations_mesh_operations_total",
        "v9_operations_mesh_readiness_assessments_total",
        "v9_operations_mesh_health_status",
    }
    assert required_metrics <= set(mesh.metrics())
    assert dashboard_snapshot(mesh)["sections"] == DASHBOARD_SECTIONS
    assert len(GET_ROUTES) == 31
    assert set(route_handlers(mesh)) == set(GET_ROUTES)
    assert all(set(value) == {"get"} for value in openapi_contract()["paths"].values())
    prohibited = (
        "execute",
        "start",
        "stop",
        "restart",
        "allocate",
        "reserve",
        "activate",
        "mutate",
        "secret",
    )
    assert not any(any(term in route for term in prohibited) for route in GET_ROUTES)
    safety_checks = (
        mesh.executes_tiktok_actions,
        mesh.mutates_runtime_state,
        mesh.starts_workflows,
        mesh.mutates_scheduler,
        mesh.mutates_services,
        mesh.allocates_resources,
        mesh.mutates_reservations,
        mesh.executes_recovery,
        mesh.activates_continuity,
        mesh.activates_maintenance,
        mesh.mutates_pause,
        mesh.mutates_killswitch,
        mesh.approves_execution,
    )
    assert not any(check() for check in safety_checks)


def test_server_integration_registers_get_only_routes() -> None:
    from server.api.app import create_app

    app = create_app()
    methods = {
        route.path: route.methods
        for route in app.routes
        if route.path.startswith("/v9/operations/")
    }
    assert set(GET_ROUTES) <= set(methods)
    assert all(value == {"GET"} for value in methods.values())
