"""Mock-only tests for the V8 Hyper Autonomous Planning Fabric."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from tkai.v8.hyper_planning.api import GET_ROUTES, openapi_contract, register_routes
from tkai.v8.hyper_planning.contracts import (
    ApprovalMetadata,
    CompatibilityMetadata,
    ConstraintKind,
    ConstraintMetadata,
    DependencyKind,
    DependencyMetadata,
    ObjectiveKind,
    ObjectiveMetadata,
    PlanMetadata,
    PlanningProfile,
    PlanningReference,
    PlanningScope,
    RecommendationMetadata,
    ResourceMetadata,
    ScenarioMetadata,
    ScheduleMetadata,
    SimulationMetadata,
)
from tkai.v8.hyper_planning.dashboard import DASHBOARD_SECTIONS, dashboard_snapshot
from tkai.v8.hyper_planning.fabric import HyperPlanningFabric
from tkai.v8.hyper_planning.security import PlanningAccessController, PlanningPrincipal


class FakeApp:
    def __init__(self) -> None:
        self.routes: dict[str, tuple[str, object]] = {}

    def add_api_route(
        self, path: str, handler: object, *, methods: list[str], tags: list[str]
    ) -> None:
        assert tags == ["V8 Hyper Planning"]
        self.routes[path] = (methods[0], handler)


def reference(identifier: str, generation: str = "v8") -> PlanningReference:
    return PlanningReference(identifier, "1.0.0", generation=generation)


def test_profile_is_complete_immutable_and_reference_only() -> None:
    profile = PlanningProfile(
        "profile-1",
        "8.0.0",
        "planning-team",
        objective_references=(reference("objective-1"),),
        constraint_references=(reference("constraint-1"),),
        scenario_references=(reference("scenario-1"),),
        simulation_references=(reference("simulation-1"),),
        resource_references=(reference("resource-1"),),
        schedule_references=(reference("schedule-1"),),
        governance_references=(reference("policy-1"),),
        compatibility_references=(reference("compatibility-1"),),
        health="healthy",
        metrics={"coverage": 1.0},
        audit=({"event": "mock-created"},),
        metadata={"classification": "internal"},
    )
    fabric = HyperPlanningFabric()
    fabric.register_profile(profile)
    serialized = fabric.snapshot()["profiles"][0]
    assert serialized["owner"] == "planning-team"
    assert serialized["execution_authorized"] is False
    with pytest.raises(FrozenInstanceError):
        profile.owner = "other"  # type: ignore[misc]


def test_objective_constraint_scenario_simulation_and_plan_metadata() -> None:
    assert set(ObjectiveKind) == set(ObjectiveKind.__members__.values())
    assert len(ObjectiveKind) == 8
    assert len(ConstraintKind) == 9
    fabric = HyperPlanningFabric()
    fabric.register_objective(
        ObjectiveMetadata("objective-1", ObjectiveKind.BUSINESS, "Mock objective")
    )
    fabric.register_constraint(
        ConstraintMetadata("constraint-1", ConstraintKind.GOVERNANCE, "Mock constraint")
    )
    fabric.register_scenario(
        ScenarioMetadata(
            "scenario-1",
            "Mock scenario",
            ("Expected outcome",),
            ("Mock risk",),
            (reference("constraint-1"),),
            (reference("simulation-1"),),
        )
    )
    fabric.register_simulation(
        SimulationMetadata(
            "simulation-1",
            "Deterministic offline summary",
            True,
            "10 units",
            "2 days",
            "none",
        )
    )
    fabric.register_plan(
        PlanMetadata(
            "plan-1",
            "Planning summary",
            "Simulation summary",
            "Evaluation summary",
            "Dependency summary",
            "Resource summary",
            "Schedule summary",
            "Recommendation summary",
            ({"version": "8.0.0"},),
        )
    )
    snapshot = fabric.snapshot()
    assert snapshot["simulations"][0]["offline_only"] is True
    assert snapshot["plans"][0]["executable"] is False
    assert fabric.diagnostics() == ()


def test_dependencies_resources_schedules_recommendations_and_compatibility() -> None:
    fabric = HyperPlanningFabric()
    for kind in DependencyKind:
        fabric.register_dependency(
            DependencyMetadata(
                f"dependency-{kind.value}",
                kind,
                reference("source"),
                reference("target"),
            )
        )
    fabric.register_resource(
        ResourceMetadata(
            "resource-1",
            "Reference only",
            {"units": 10},
            {"window": "mock"},
            {"status": "unreserved"},
        )
    )
    fabric.register_schedule(
        ScheduleMetadata(
            "schedule-1",
            "Reference only",
            ("mock-window",),
            "2 days",
            ("mock-milestone",),
        )
    )
    recommendation = RecommendationMetadata("recommendation-1", "Human review advised")
    fabric.register_recommendation(recommendation)
    for generation in ("v6", "v7", "v8"):
        fabric.register_compatibility(
            CompatibilityMetadata(
                f"compatibility-{generation}",
                reference(f"{generation}-source", generation),
                reference("v8-planning", "v8"),
            )
        )
    snapshot = fabric.snapshot()
    assert snapshot["resources"][0]["allocated"] is False
    assert snapshot["schedules"][0]["scheduler_mutated"] is False
    assert recommendation.advisory is True
    assert recommendation.execution_authorized is False
    assert fabric.metrics()["compatibility"] == 3
    from tkai.v7.ai_framework import UnifiedAIFramework
    from tkai.v8.hyper_decision import HyperDecisionFabric

    assert UnifiedAIFramework is not None
    assert HyperDecisionFabric is not None


def test_security_isolation_filtering_observability_and_approval_guard() -> None:
    fabric = HyperPlanningFabric(metadata={"api_key": "mock-secret", "visible": "safe"})
    scope = PlanningScope("tenant-a", "workspace-a", "domain-a")
    principal = PlanningPrincipal(
        "reader",
        frozenset({"planning:read"}),
        "tenant-a",
        "workspace-a",
        frozenset({"domain-a"}),
    )
    controller = PlanningAccessController()
    controller.authorize(principal, "planning:read", scope)
    for invalid in (
        PlanningScope("tenant-b", "workspace-a", "domain-a"),
        PlanningScope("tenant-a", "workspace-b", "domain-a"),
        PlanningScope("tenant-a", "workspace-a", "domain-b"),
    ):
        with pytest.raises(PermissionError):
            controller.authorize(principal, "planning:read", invalid)
    approval = ApprovalMetadata(
        "approval-1", reference("plan-1"), status="metadata-approved"
    )
    fabric.register_approval(approval)
    fabric.observability.log("info", "mock log", {"token": "hidden"})
    fabric.observability.trace("planning-read", "mock-correlation")
    assert fabric.metadata["api_key"] == "[REDACTED]"
    assert fabric.snapshot()["logs"][0]["metadata"]["token"] == "[REDACTED]"
    assert fabric.snapshot()["traces"]
    assert fabric.snapshot()["audit"]
    assert approval.authorizes_execution is False
    with pytest.raises(ValueError, match="prohibited"):
        PlanningProfile("bad", "8", "owner", metadata={"execute": True})


def test_dashboard_health_metrics_api_and_non_execution_guards() -> None:
    fabric = HyperPlanningFabric()
    dashboard = dashboard_snapshot(fabric)
    assert dashboard["read_only"] is True
    assert len(DASHBOARD_SECTIONS) == 12
    assert fabric.health()["status"] == "healthy"
    assert fabric.executes_tiktok_actions() is False
    assert fabric.mutates_runtime_state() is False
    assert fabric.schedules_runtime_work() is False
    assert fabric.allocates_resources() is False
    assert fabric.authorizes_execution() is False
    assert fabric.automatically_approves() is False
    app = FakeApp()
    register_routes(app, fabric)
    assert set(app.routes) == set(GET_ROUTES)
    assert {method for method, _ in app.routes.values()} == {"GET"}
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    assert set(paths) == set(GET_ROUTES)
    assert all(set(operation) == {"get"} for operation in paths.values())
    assert not any(
        term in path
        for path in GET_ROUTES
        for term in ("execute", "schedule-runtime", "automatic-approval")
    )


def test_cross_version_aggregation_is_reference_only() -> None:
    fabric = HyperPlanningFabric()
    sources = fabric.aggregate_metadata(
        v6_ai_centers=({"id": "v6-center", "token": "hidden"},),
        v7_frameworks=({"id": "v7-framework"},),
        v8_frameworks=({"id": "v8-framework"},),
    )
    assert sources["v6_ai_centers"][0]["token"] == "[REDACTED]"
    assert fabric.metrics()["aggregated_references"] == 3
