from __future__ import annotations

import importlib
from dataclasses import FrozenInstanceError, replace

import pytest

from tkai.v7.security import AccessController, Principal
from tkai.v7.workflow_framework import (
    Constraint,
    Dependency,
    DependencyCycleError,
    IllegalLifecycleTransition,
    ScheduleMetadata,
    Workflow,
    WorkflowFramework,
    WorkflowLifecycle,
    WorkflowScope,
    WorkflowSecurity,
    WorkflowValidationError,
)
from tkai.v7.workflow_framework.api import (
    WORKFLOW_RESOURCES,
    register_workflow_framework_routes,
)
from tkai.v7.workflow_framework.dashboard import WorkflowDashboard


def workflow(
    workflow_id: str = "workflow-1",
    *,
    dependencies: tuple[Dependency, ...] = (),
    constraints: tuple[Constraint, ...] = (),
    scope: WorkflowScope | None = None,
    schedule: ScheduleMetadata | None = None,
) -> Workflow:
    return Workflow(
        workflow_id=workflow_id,
        name=workflow_id,
        version="1.0.0",
        owner="kernel",
        category="internal",
        definition={"reference": f"definition://{workflow_id}", "token": "secret"},
        state_reference=f"state://{workflow_id}",
        scope=scope or WorkflowScope("tenant-1", "workspace-1"),
        dependencies=dependencies,
        constraints=constraints,
        schedule=schedule or ScheduleMetadata(),
        metadata={"api_key": "secret", "safe": "visible"},
    )


def test_required_packages_are_importable() -> None:
    packages = (
        "definitions registry planner orchestrator scheduler dependencies constraints "
        "transitions validation snapshots history recovery contracts interfaces events "
        "state health metrics audit security lifecycle dashboard api"
    ).split()
    for package in packages:
        assert importlib.import_module(f"tkai.v7.workflow_framework.{package}")


def test_registry_definition_immutability_and_secret_filtering() -> None:
    framework = WorkflowFramework()
    item = framework.register(workflow())
    assert framework.registry.get(item.workflow_id) == item
    assert item.definition["token"] == "[REDACTED]"
    assert item.metadata["api_key"] == "[REDACTED]"
    with pytest.raises(FrozenInstanceError):
        item.name = "changed"  # type: ignore[misc]
    with pytest.raises(WorkflowValidationError):
        framework.register(workflow())


def test_planner_is_deterministic_bounded_and_reference_only() -> None:
    framework = WorkflowFramework(max_plan_size=3)
    framework.register(workflow("a"))
    framework.register(workflow("b", dependencies=(Dependency("a"),)))
    framework.register(workflow("c", dependencies=(Dependency("b"), Dependency("a"))))
    first = framework.plan("c")
    second = framework.orchestrate("c")
    assert first.ordered_workflow_ids == second.ordered_workflow_ids == ("a", "b", "c")
    assert first.ready and first.bounded and first.reference_only
    assert not hasattr(framework, "execute")


def test_validation_covers_dependencies_constraints_version_state_schedule() -> None:
    framework = WorkflowFramework()
    bad = replace(
        workflow(
            dependencies=(Dependency("missing"),),
            constraints=(Constraint("approval", satisfied=False),),
            schedule=ScheduleMetadata("2027-02-01", "2027-01-01", 101),
        ),
        version="latest",
        state_reference="inline state",
    )
    framework.register(bad)
    codes = {issue.code for issue in framework.validate("workflow-1").issues}
    assert codes == {
        "constraint_unsatisfied",
        "dependency_missing",
        "schedule_priority_invalid",
        "schedule_window_invalid",
        "state_reference_invalid",
        "version_invalid",
    }


def test_dependency_cycle_is_rejected() -> None:
    framework = WorkflowFramework()
    framework.register(workflow("a", dependencies=(Dependency("b"),)))
    framework.register(workflow("b", dependencies=(Dependency("a"),)))
    with pytest.raises(DependencyCycleError):
        framework._ordered_dependencies("a")
    assert not framework.plan("a").ready


def test_lifecycle_is_explicit_and_has_no_runtime_side_effect() -> None:
    framework = WorkflowFramework()
    framework.register(workflow())
    updated = framework.transition("workflow-1", WorkflowLifecycle.VALIDATED)
    assert updated.lifecycle is WorkflowLifecycle.VALIDATED
    with pytest.raises(IllegalLifecycleTransition):
        framework.transition("workflow-1", WorkflowLifecycle.QUEUED)


def test_recovery_and_rollback_are_reference_only() -> None:
    framework = WorkflowFramework()
    original = framework.register(workflow())
    recovery = framework.plan_recovery("workflow-1", "snapshot://workflow-1/v1")
    rollback = framework.plan_recovery(
        "workflow-1", "snapshot://workflow-1/v0", rollback=True
    )
    assert recovery.ready and recovery.coordinated and recovery.reference_only
    assert rollback.rollback
    assert framework.registry.get("workflow-1") == original


def test_security_rbac_tenant_workspace_and_workflow_isolation() -> None:
    access = AccessController({"operator": {"workflow.transition"}})
    security = WorkflowSecurity(access)
    framework = WorkflowFramework(security=security)
    item = framework.register(workflow())
    principal = Principal("operator", frozenset({"operator"}))
    with pytest.raises(PermissionError, match="tenant"):
        framework.transition(
            item.workflow_id,
            WorkflowLifecycle.VALIDATED,
            principal=principal,
            tenant_reference="other",
        )
    with pytest.raises(PermissionError, match="lacks"):
        framework.transition(
            item.workflow_id,
            WorkflowLifecycle.VALIDATED,
            principal=Principal("viewer", frozenset({"viewer"})),
        )
    with pytest.raises(PermissionError, match="workflow"):
        security.authorize(
            item, "workflow.transition", principal=principal, owner="other"
        )


def test_metrics_audit_tracing_health_and_history() -> None:
    framework = WorkflowFramework()
    traces: list[str] = []
    framework.tracing.register(lambda name, _attributes: traces.append(name))
    framework.register(workflow(), actor="tester")
    framework.plan("workflow-1", actor="tester")
    projection = framework.snapshot()
    health = projection["health"]
    metrics = projection["metrics"]
    assert isinstance(health, dict) and health["execution_enabled"] is False
    assert isinstance(metrics, dict) and metrics["v7_workflow_plans_total"] == 1
    assert projection["history"] == projection["audit"]
    assert traces == ["workflow.registered", "workflow.planned"]
    assert framework.logs


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, _endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.append((path, tuple(methods)))


def test_api_is_get_only_and_dashboard_has_required_sections() -> None:
    framework = WorkflowFramework()
    app = FakeApp()
    register_workflow_framework_routes(app, framework)
    assert {path for path, _ in app.routes} == {
        f"/v7/workflows/{resource}" for resource in WORKFLOW_RESOURCES
    }
    assert all(methods == ("GET",) for _, methods in app.routes)
    dashboard = WorkflowDashboard(framework)
    assert set(dashboard.snapshot()) == set(dashboard.sections)


def test_v6_and_previous_v7_imports_are_unchanged() -> None:
    assert importlib.import_module("tiktok.workflow_center")
    assert importlib.import_module("tkai.v7.state_framework")
    assert importlib.import_module("tkai.v7.event_fabric")
    assert importlib.import_module("tkai.v7.service_mesh")
