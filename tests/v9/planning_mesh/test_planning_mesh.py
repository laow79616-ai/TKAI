from dataclasses import FrozenInstanceError

import pytest

from tkai.v9.planning_mesh import (
    AdaptivePlanningMesh,
    Compatibility,
    Constraint,
    Dependency,
    Evaluation,
    Objective,
    Plan,
    PlanningScope,
    Profile,
    Recommendation,
    Reference,
    Resource,
    Scenario,
    Schedule,
    Simulation,
)
from tkai.v9.planning_mesh.api import GET_ROUTES, openapi_contract, route_handlers
from tkai.v9.planning_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v9.planning_mesh.security import authorize


def reference(identifier: str = "ref-1", framework: str = "v9_components") -> Reference:
    return Reference(identifier, generation="v9", framework=framework)


def test_profile_is_complete_immutable_and_non_executable() -> None:
    ref = reference()
    profile = Profile(
        "profile-1",
        "9.0.0",
        "owner",
        (ref,),
        (ref,),
        (ref,),
        (ref,),
        (ref,),
        (ref,),
        (ref,),
        (ref,),
        health="healthy",
        metrics={"count": 1},
        metadata={"safe": True},
    )
    assert profile.execution_authorized is False
    assert profile.metadata["safe"] is True
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_federation_is_bounded_allowlisted_local_and_reference_only() -> None:
    mesh = AdaptivePlanningMesh(maximum_sources=1)
    assert mesh.federate((reference(),))[0].identifier == "ref-1"
    assert mesh.federation.mutates_upstream() is False
    with pytest.raises(ValueError, match="bounded"):
        mesh.federate((reference("one"), reference("two")))
    with pytest.raises(ValueError, match="allowlisted"):
        AdaptivePlanningMesh().federate((reference(framework="unknown"),))
    with pytest.raises(ValueError, match="network"):
        AdaptivePlanningMesh().federate(
            (Reference("remote", framework="v8_frameworks", metadata={"remote": True}),)
        )


def test_all_planning_metadata_records_and_summaries() -> None:
    mesh = AdaptivePlanningMesh()
    records = (
        ("objectives", Objective("objective-1", "business", "Grow safely")),
        ("constraints", Constraint("constraint-1", "security", "Keep isolated")),
        ("plans", Plan("plan-1", "Advisory plan")),
        ("scenarios", Scenario("scenario-1", "Expected", ("Stable",), ("Offline",))),
        ("simulations", Simulation("simulation-1", "Deterministic result")),
        ("dependencies", Dependency("dependency-1", "framework", "V8 dependency")),
        ("resources", Resource("resource-1", "Forecast", {"units": 10})),
        ("schedules", Schedule("schedule-1", "Window", ("review",), "2 days")),
        ("evaluations", Evaluation("evaluation-1", "Viable")),
        ("recommendations", Recommendation("recommendation-1", "Review manually")),
        ("compatibility_records", Compatibility("compat-1", "v6", reference())),
    )
    for name, record in records:
        mesh.register(name, record)
    snapshot = mesh.snapshot()
    assert snapshot["plans"][0]["executable"] is False
    assert snapshot["simulations"][0]["executes_runtime"] is False
    assert snapshot["resources"][0]["allocated"] is False
    assert snapshot["schedules"][0]["scheduler_mutated"] is False
    assert snapshot["recommendations"][0]["advisory"] is True
    assert snapshot["compatibility"][0]["generation"] == "v6"


@pytest.mark.parametrize(
    "category",
    (
        "governance",
        "security",
        "runtime",
        "resources",
        "schedules",
        "dependencies",
        "risk",
        "compatibility",
        "pause",
        "maintenance",
        "kill_switch",
    ),
)
def test_all_constraint_categories(category: str) -> None:
    assert Constraint("constraint", category, "Reference-only")


def test_security_isolates_tenant_workspace_and_planning_scope() -> None:
    actual = PlanningScope("tenant-a", "workspace-a", "planning-a")
    assert authorize("read", actual, actual)
    assert authorize("review", actual, PlanningScope("tenant-a", "workspace-a"))
    assert not authorize("execute", actual, actual)
    assert not authorize("read", actual, PlanningScope("tenant-b", "workspace-a"))
    assert not authorize("read", actual, PlanningScope("tenant-a", "workspace-b"))


def test_secret_filtering_is_recursive() -> None:
    with pytest.raises(ValueError, match="secret"):
        Profile("p", "9", "owner", metadata={"nested": {"api_key": "no"}})


def test_health_metrics_dashboard_and_audit() -> None:
    mesh = AdaptivePlanningMesh()
    assert mesh.health()["status"] == "healthy"
    assert mesh.metrics()["v9_planning_mesh_execution_total"] == 0
    assert mesh.metrics()["v9_planning_mesh_resource_allocations_total"] == 0
    assert mesh.metrics()["v9_planning_mesh_scheduler_mutations_total"] == 0
    dashboard = dashboard_snapshot(mesh)
    assert dashboard["sections"] == DASHBOARD_SECTIONS
    assert "Planning Mesh Overview" in DASHBOARD_SECTIONS
    assert dashboard["audit"]


def test_api_is_get_only_and_has_no_mutation_endpoint() -> None:
    mesh = AdaptivePlanningMesh()
    required = {
        "/v9/planning/profiles",
        "/v9/planning/objectives",
        "/v9/planning/constraints",
        "/v9/planning/scenarios",
        "/v9/planning/simulations",
        "/v9/planning/dependencies",
        "/v9/planning/resources",
        "/v9/planning/schedules",
        "/v9/planning/recommendations",
        "/v9/planning/compatibility",
        "/v9/planning/health",
        "/v9/planning/metrics",
    }
    assert required <= set(GET_ROUTES)
    assert set(route_handlers(mesh)) == set(GET_ROUTES)
    paths = openapi_contract()["paths"]
    assert all(set(operation) == {"get"} for operation in paths.values())
    prohibited = ("execute", "allocate", "schedule-work", "mutate", "trigger")
    assert not any(any(word in path for word in prohibited) for path in paths)
    assert not mesh.executes_tiktok_actions()
    assert not mesh.mutates_runtime_state()
    assert not mesh.allocates_resources()
    assert not mesh.mutates_scheduler()
    assert not mesh.triggers_workflows()
    assert not mesh.approves_execution()
