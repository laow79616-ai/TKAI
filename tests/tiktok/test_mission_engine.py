from datetime import timedelta

import pytest

from tiktok.mission_engine.adapters import INTEGRATION_MODULES
from tiktok.mission_engine.api import ROUTES, register_mission_engine_routes
from tiktok.mission_engine.metrics import METRIC_NAMES
from tiktok.mission_engine.models import (
    ApprovalState,
    ExecutionWindow,
    Mission,
    MissionScope,
    MissionState,
    RiskState,
    utcnow,
)
from tiktok.mission_engine.service import TikTokAutonomousMissionEngine


class Module:
    def __init__(self, **health: object) -> None:
        self.health_value = {"healthy": True, **health}
        self.actions: list[str] = []

    def health(self, mission_id: str, scope: MissionScope) -> dict[str, object]:
        return dict(self.health_value)

    def dispatch(self, mission: Mission, scope: MissionScope) -> str:
        self.actions.append("dispatch")
        return f"existing://{mission.id}"

    def resume(self, mission_id: str, checkpoint: str, scope: MissionScope) -> str:
        self.actions.append("resume")
        return f"existing://{mission_id}/resume/{checkpoint}"

    def rollback(self, mission_id: str, scope: MissionScope) -> None:
        self.actions.append("rollback")

    def recover(self, mission_id: str, scope: MissionScope) -> str:
        self.actions.append("recover")
        return f"existing://{mission_id}/recover"


def scope(workspace: str = "workspace") -> MissionScope:
    return MissionScope(
        "tenant",
        workspace,
        "operator",
        frozenset({"tiktok:mission-engine:admin"}),
    )


def mission(
    reference: str = "mission-1",
    *,
    dependencies: tuple[str, ...] = (),
    workspace: str = "workspace",
) -> Mission:
    now = utcnow()
    return Mission(
        reference,
        f"autonomous://{reference}",
        "tenant",
        workspace,
        2,
        dependencies,
        ApprovalState.APPROVED,
        RiskState.CLEAR,
        ExecutionWindow(now - timedelta(minutes=1), now + timedelta(hours=1)),
        {"operation": "bounded-workflow"},
    )


def test_queue_priority_dependencies_dispatch_and_delegation() -> None:
    modules = {name: Module() for name in INTEGRATION_MODULES}
    service = TikTokAutonomousMissionEngine(modules)
    dependency = mission("dependency")
    dependent = mission("dependent", dependencies=("dependency",))
    dependent.priority = 1
    service.enqueue(dependency, scope())
    service.enqueue(dependent, scope())
    assert [item.id for item in service.queue(scope())] == [
        "dependent",
        "dependency",
    ]
    with pytest.raises(RuntimeError, match="dependencies"):
        service.dispatch("dependent", scope(), worker="worker-1")
    service.dispatch("dependency", scope(), worker="worker-1", queue="critical")
    service.complete("dependency", scope())
    dispatched = service.dispatch("dependent", scope(), worker="worker-2")
    assert dispatched.state is MissionState.RUNNING
    assert dispatched.queue == "default"
    expected = set(INTEGRATION_MODULES) - {
        "autonomous_operation",
        "risk_control",
    }
    assert set(dispatched.delegated) == expected


def test_approval_risk_window_scope_rbac_and_secret_enforcement() -> None:
    service = TikTokAutonomousMissionEngine()
    pending = mission()
    pending.approval_state = ApprovalState.PENDING
    with pytest.raises(PermissionError, match="Approved"):
        service.enqueue(pending, scope())
    restricted = mission()
    restricted.risk_state = RiskState.RESTRICTED
    with pytest.raises(PermissionError, match="risk"):
        service.enqueue(restricted, scope())
    unsafe = mission()
    unsafe.payload = {"token": "not-logged"}
    with pytest.raises(ValueError, match="Secrets"):
        service.enqueue(unsafe, scope())
    service.enqueue(mission(), scope())
    with pytest.raises(PermissionError, match="Cross-tenant"):
        service.dispatch("mission-1", scope("other"), worker="worker")
    read_only = MissionScope("tenant", "workspace", "viewer")
    with pytest.raises(PermissionError, match="RBAC"):
        service.dispatch("mission-1", read_only, worker="worker")


def test_monitoring_checkpoint_retry_recovery_and_rollback() -> None:
    modules = {name: Module() for name in INTEGRATION_MODULES}
    service = TikTokAutonomousMissionEngine(modules)
    service.enqueue(mission(), scope())
    service.dispatch("mission-1", scope(), worker="worker")
    health = service.health("mission-1", scope())
    assert all(
        health[key]
        for key in (
            "runtime_health",
            "execution_health",
            "resource_health",
            "recovery_health",
        )
    )
    service.checkpoint("mission-1", "checkpoint-1", 0.5, scope())
    service.fail("mission-1", "mock failure", scope())
    recovered = service.recover("mission-1", scope())
    assert recovered.state is MissionState.RUNNING
    assert all(
        "resume" in module.actions
        for name, module in modules.items()
        if name not in {"autonomous_operation", "risk_control"}
    )
    service.fail("mission-1", "mock failure", scope())
    rolled_back = service.recover("mission-1", scope(), rollback=True)
    assert rolled_back.state is MissionState.ROLLED_BACK


def test_unresolved_restrictions_stop_dispatch_and_recovery() -> None:
    modules = {name: Module() for name in INTEGRATION_MODULES}
    modules["risk_control"] = Module(restriction_unresolved=True)
    service = TikTokAutonomousMissionEngine(modules)
    service.enqueue(mission(), scope())
    with pytest.raises(PermissionError, match="restriction"):
        service.dispatch("mission-1", scope(), worker="worker")
    modules["risk_control"] = Module()
    service.modules["risk_control"] = modules["risk_control"]
    service.dispatch("mission-1", scope(), worker="worker")
    service.fail("mission-1", "mock failure", scope())
    service.modules["risk_control"] = Module(challenge_unresolved=True)
    with pytest.raises(PermissionError, match="restriction"):
        service.recover("mission-1", scope())


def test_api_dashboard_analytics_metrics_and_openapi_contracts() -> None:
    class App:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def add_api_route(self, path: str, endpoint: object, **kwargs: object) -> None:
            self.paths.append(path)

    service = TikTokAutonomousMissionEngine()
    service.enqueue(mission(), scope())
    dashboard = service.dashboard(scope())
    assert dashboard["sections"] == [
        "mission_queue",
        "mission_health",
        "dispatch",
        "recovery",
        "analytics",
    ]
    assert service.analytics(scope())["total"] == 1
    rendered = service.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
    app = App()
    register_mission_engine_routes(app, service)
    assert set(ROUTES).issubset(app.paths)
    assert "/tiktok/mission-engine/dashboard" in app.paths
    assert "/tiktok/mission-engine/metrics" in app.paths
