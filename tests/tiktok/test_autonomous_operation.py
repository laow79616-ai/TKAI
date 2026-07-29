from datetime import timedelta

import pytest

from tiktok.autonomous_operation.adapters import DELEGATION_MODULES
from tiktok.autonomous_operation.api import ROUTES
from tiktok.autonomous_operation.metrics import METRIC_NAMES
from tiktok.autonomous_operation.models import (
    Constraint,
    ConstraintType,
    Mission,
    MissionApproval,
    MissionPlan,
    MissionStatus,
    MissionType,
    Objective,
    ObjectiveType,
    OperationScope,
    PlanningHorizon,
    Policy,
    PolicyType,
    utcnow,
)
from tiktok.autonomous_operation.service import TikTokAutonomousOperationCenter


class Delegate:
    def __init__(self, **health: object) -> None:
        self.health_value = {"healthy": True, **health}
        self.actions: list[str] = []

    def dispatch(
        self, mission: Mission, plan: MissionPlan, scope: OperationScope
    ) -> str:
        self.actions.append("dispatch")
        return f"accepted://{mission.id}/{plan.id}"

    def pause(self, mission_id: str, scope: OperationScope) -> None:
        self.actions.append("pause")

    def resume(self, mission_id: str, checkpoint: str, scope: OperationScope) -> str:
        self.actions.append("resume")
        return f"resumed://{mission_id}/{checkpoint}"

    def rollback(self, mission_id: str, reference: str, scope: OperationScope) -> None:
        self.actions.append("rollback")

    def health(self, mission_id: str, scope: OperationScope) -> dict[str, object]:
        return dict(self.health_value)


def scope(workspace: str = "workspace") -> OperationScope:
    return OperationScope(
        "tenant",
        workspace,
        "operator",
        frozenset({"tiktok:autonomous:admin"}),
    )


def mission(reference: str = "m", workspace: str = "workspace") -> Mission:
    return Mission(
        reference,
        "Publishing reliability",
        "Bounded daily operation",
        "tenant",
        workspace,
        2,
        PlanningHorizon.DAILY,
        "owner",
        MissionType.MIXED,
        [Objective(ObjectiveType.PUBLISHING_STABILITY, 99, "percent")],
        [
            Policy(PolicyType.APPROVAL, {"required": True}),
            Policy(PolicyType.RISK, {"maximum": "low"}),
        ],
        [Constraint(ConstraintType.QUEUE_CAPACITY, 10, "tasks")],
    )


def prepare(
    service: TikTokAutonomousOperationCenter,
    reference: str = "m",
) -> None:
    service.create_mission(mission(reference), scope())
    service.add_plan(
        MissionPlan(
            f"plan-{reference}",
            reference,
            "tenant",
            "workspace",
            ["task://1"],
            "checkpoint-1",
            "rollback://1",
        ),
        scope(),
    )
    service.approve(
        MissionApproval(
            f"approval-{reference}",
            reference,
            "tenant",
            "workspace",
            "reviewer",
            True,
            utcnow() + timedelta(hours=1),
        ),
        scope(),
    )
    service.ready(reference, scope())


def test_mission_lifecycle_delegates_to_every_existing_engine() -> None:
    delegates = {name: Delegate() for name in DELEGATION_MODULES}
    service = TikTokAutonomousOperationCenter(delegates)
    prepare(service)
    execution = service.dispatch("m", scope())
    assert service.missions["m"].status is MissionStatus.RUNNING
    assert set(execution.delegated_references) == set(DELEGATION_MODULES)
    service.checkpoint("m", "checkpoint-2", scope())
    service.pause("m", scope())
    service.resume("m", scope())
    service.complete("m", scope())
    assert service.missions["m"].status is MissionStatus.COMPLETED
    assert all("dispatch" in delegate.actions for delegate in delegates.values())


def test_approval_isolation_bounds_and_secret_guards() -> None:
    service = TikTokAutonomousOperationCenter()
    unsafe = mission()
    unsafe.metadata = {"token": "forbidden"}
    with pytest.raises(ValueError, match="Secrets"):
        service.create_mission(unsafe, scope())
    service.create_mission(mission(), scope())
    with pytest.raises(PermissionError, match="Cross-tenant"):
        service.transition("m", MissionStatus.PLANNED, scope("other"))
    with pytest.raises(ValueError, match="Invalid"):
        service.transition("m", MissionStatus.READY, scope())


def test_monitor_recovery_rollback_and_analytics() -> None:
    delegates = {
        name: Delegate(resource_usage=1.0, queue_state="ready")
        for name in DELEGATION_MODULES
    }
    service = TikTokAutonomousOperationCenter(delegates)
    prepare(service)
    service.dispatch("m", scope())
    monitoring = service.monitor("m", scope())
    assert monitoring["resource_usage"] == len(DELEGATION_MODULES)
    service.recover("m", scope())
    assert service.executions["m"].recovery_state == "recovering"
    service.resume("m", scope())
    service.rollback("m", scope())
    analytics = service.analytics(scope())
    assert analytics["mission_count"] == 1
    assert analytics["mission_recovery"] == 1


def test_unresolved_tiktok_restrictions_stop_dispatch_and_recovery() -> None:
    delegates = {name: Delegate() for name in DELEGATION_MODULES}
    delegates["runtime_manager"] = Delegate(restriction_unresolved=True)
    service = TikTokAutonomousOperationCenter(delegates)
    prepare(service)
    with pytest.raises(PermissionError, match="restriction"):
        service.dispatch("m", scope())


def test_dashboard_api_and_metrics_contracts() -> None:
    service = TikTokAutonomousOperationCenter()
    service.create_mission(mission(), scope())
    dashboard = service.dashboard(scope())
    assert len(ROUTES) == 5
    assert dashboard["title"] == "TikTok Autonomous Operation Center"
    assert set(
        (
            "Mission Overview",
            "Plans",
            "Objectives",
            "Policies",
            "Constraints",
            "Execution",
            "Monitoring",
            "Recovery",
            "Analytics",
        )
    ).issubset(dashboard["sections"])
    rendered = service.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)


def test_api_registration_uses_required_roots() -> None:
    from tiktok.autonomous_operation.api import register_autonomous_operation_routes

    class App:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def add_api_route(self, path: str, endpoint: object, **kwargs: object) -> None:
            self.paths.append(path)

    app = App()
    register_autonomous_operation_routes(app, TikTokAutonomousOperationCenter())
    assert set(ROUTES).issubset(app.paths)
    assert "/tiktok/autonomous-operation/dashboard" in app.paths
    assert "/tiktok/autonomous-operation/metrics" in app.paths
