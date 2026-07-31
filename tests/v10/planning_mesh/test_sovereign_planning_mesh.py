"""Offline mock-only tests for the V10 Sovereign Planning Mesh."""
# ruff: noqa: E501

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from tkai.v10.contracts import Scope
from tkai.v10.planning_mesh import (
    Dependency,
    DependencyType,
    Milestone,
    Objective,
    ObjectiveStatus,
    PlanningContext,
    PlanningProfile,
    PlanningReadiness,
    PlanningValidation,
    ReadinessStatus,
    SovereignPlanningMesh,
    Timeline,
    TimelineStatus,
    ValidationType,
)
from tkai.v10.planning_mesh.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v10.planning_mesh.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v10.planning_mesh.security import authorize_metadata_read


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
        """profiles registry contexts objectives milestones dependencies timelines assumptions
        constraints risks alternatives plans readiness validation compatibility governance
        integrity trust reasoning decision knowledge diagnostics health metrics audit security
        events contracts interfaces lifecycle dashboard api""".split()
    )
    package = root / "src/tkai/v10/planning_mesh"
    assert required <= {path.name for path in package.iterdir() if path.is_dir()}
    profile = PlanningProfile("profile", "subject", safe_metadata={"label": "safe"})
    with pytest.raises(FrozenInstanceError):
        profile.health = "bad"  # type: ignore[misc]
    mesh = SovereignPlanningMesh()
    mesh.register("profiles", profile)
    assert {item.generation for item in mesh.discover("compatibility")} == {
        "v6", "v7", "v8", "v9", "v10"
    }


def test_contexts_objectives_milestones_timelines_dependencies() -> None:
    mesh = SovereignPlanningMesh()
    records = (
        ("contexts", PlanningContext("context", "subject", "bounded", "tenant", "workspace")),
        ("objectives", Objective("objective", "subject", "metadata goal", ObjectiveStatus.CANDIDATE)),
        ("milestones", Milestone("milestone", "objective", ("dependency",), ("validation",), ("readiness",), "audit")),
        ("timelines", Timeline("timeline", "objective", TimelineStatus.TENTATIVE)),
        ("dependencies", Dependency("dependency", "objective", "v10:core", DependencyType.FRAMEWORK)),
    )
    for registry, record in records:
        mesh.register(registry, record)
    assert len(ObjectiveStatus) == 6
    assert len(TimelineStatus) == 5
    assert len(DependencyType) == 10
    assert all(mesh.discover(registry) for registry, _ in records)


def test_readiness_validation_and_metadata_only_guards() -> None:
    mesh = SovereignPlanningMesh()
    readiness = PlanningReadiness("ready", "objective", ReadinessStatus.REVIEW_REQUIRED)
    validation = PlanningValidation("validation", "objective", ValidationType.OBJECTIVE)
    mesh.register("readiness", readiness)
    mesh.register("validation", validation)
    assert len(ReadinessStatus) == 5
    assert len(ValidationType) == 12
    assert readiness.metadata_only and validation.metadata_only
    assert not any(hasattr(mesh, name) for name in ("execute", "schedule", "allocate"))


def test_bounds_rbac_tenant_isolation_secrets_and_hidden_reasoning() -> None:
    mesh = SovereignPlanningMesh(per_registry_limit=5)
    scope = Scope("tenant", "workspace")
    authorize_metadata_read(scope, scope, role_references=("reader",))
    with pytest.raises(PermissionError):
        authorize_metadata_read(scope, scope)
    with pytest.raises(ValueError, match="hidden"):
        mesh.register(
            "profiles",
            PlanningProfile("bad", "subject", safe_metadata={"chain_of_thought": "secret"}),
        )
    assert mesh.serialize({"api_key": "secret"}) == {"api_key": "[REDACTED]"}
    with pytest.raises(ValueError, match="between 0 and 100"):
        mesh.discover("profiles", limit=101)


def test_dashboard_health_metrics_audit_and_integrations() -> None:
    mesh = SovereignPlanningMesh()
    mesh.register("profiles", PlanningProfile("profile", "subject"))
    snapshot = dashboard_snapshot(mesh)
    assert mesh.health()["readiness"]
    assert mesh.metrics()["v10_planning_profiles_total"] == 1
    assert len(mesh.metrics()) == 10
    assert len(DASHBOARD_SECTIONS) == 10
    assert snapshot["actions"] == ()
    assert len(mesh.overview()["integrations"]) == 8
    assert mesh.audit()


def test_api_and_openapi_are_exactly_ten_get_only_routes() -> None:
    app = FakeApp()
    register_routes(app)
    assert len(GET_ROUTES) == 10
    assert {method for method, _ in app.routes.values()} == {"GET"}
    assert all(set(operations) == {"get"} for operations in openapi_contract()["paths"].values())
    assert set(GET_ROUTES) == {
        f"/v10/planning/{name}"
        for name in (
            "profiles", "contexts", "objectives", "milestones", "dependencies",
            "timelines", "readiness", "validation", "health", "metrics",
        )
    }
    root = Path(__file__).resolve().parents[3]
    assert "register_v10_sovereign_planning_mesh_routes(app)" in (
        root / "server/api/app.py"
    ).read_text()


def test_no_execution_scheduler_resource_write_or_hidden_reasoning_endpoints() -> None:
    mesh = SovereignPlanningMesh()
    forbidden = (
        "execute", "apply", "schedule", "scheduler", "allocate", "resource", "mutate",
        "write", "create", "update", "delete", "post", "put", "patch", "deploy",
        "chain-of-thought", "scratchpad", "hidden-prompt",
    )
    assert not any(any(term in path for term in forbidden) for path in GET_ROUTES)
    assert all(value is False for value in mesh.diagnostics().values())
    assert mesh.overview()["execution"] == "disabled"
    assert mesh.overview()["scheduler"] == "disconnected"
    assert mesh.overview()["resource_allocation"] is False
