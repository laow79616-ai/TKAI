from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from tiktok.operations_center import (
    HIGH_RISK_ACTIONS,
    ActionKind,
    AlertStatus,
    Approval,
    OperationsAlert,
    OperationsCenter,
    OperationsIncident,
    OperationsScope,
    OperationsStatus,
    OperationsTask,
    RecoveryRequest,
    TikTokOperationsCommandCenter,
)
from tiktok.operations_center.api import ROUTES, register_operations_center_routes
from tiktok.operations_center.metrics import METRIC_NAMES
from tiktok.operations_center.models import utcnow


class Port:
    def __init__(self, state: dict[str, Any] | None = None) -> None:
        self.state = state or {"status": "healthy", "healthy": 1, "unhealthy": 0}
        self.calls: list[tuple[str, str]] = []

    def status(self, scope: OperationsScope) -> dict[str, Any]:
        return self.state

    def execute(
        self, action: str, resource_reference: str, scope: OperationsScope
    ) -> dict[str, Any]:
        self.calls.append((action, resource_reference))
        return {"accepted": True}


def scope(workspace: str = "w1") -> OperationsScope:
    return OperationsScope(
        "tenant-1",
        workspace,
        "operator",
        frozenset({"tiktok:operations:admin"}),
    )


def test_lifecycle_rbac_isolation_and_secret_validation() -> None:
    service = TikTokOperationsCommandCenter()
    item = service.create_center(
        OperationsCenter("ops-1", "Operations", "", "tenant-1", "w1", "owner"),
        scope(),
    )
    assert service.transition(item.id, OperationsStatus.ACTIVE, scope()).version == 2
    with pytest.raises(PermissionError):
        service.transition(item.id, OperationsStatus.PAUSED, scope("other"))
    with pytest.raises(ValueError):
        service.create_center(
            OperationsCenter(
                "bad",
                "Bad",
                "",
                "tenant-1",
                "w1",
                "owner",
                metadata={"cookie": "plaintext"},
            ),
            scope(),
        )


def test_overview_unified_health_tasks_alerts_incidents_and_dashboard() -> None:
    ports = {
        "accounts": Port(
            {
                "status": "degraded",
                "total": 5,
                "active": 3,
                "paused": 1,
                "restricted": 1,
            }
        ),
        "browsers": Port({"status": "healthy", "active": 2, "failures": 0}),
        "proxies": Port({"status": "healthy", "healthy": 4, "unhealthy": 1}),
        "workflows": Port({"status": "healthy", "running": 2}),
        "publishing": Port({"status": "healthy", "jobs": 3}),
        "collection": Port({"status": "healthy", "jobs": 4}),
        "interaction": Port({"status": "healthy", "tasks": 6}),
    }
    service = TikTokOperationsCommandCenter(ports)
    service.register_task(
        OperationsTask("task-1", "tenant-1", "w1", "manual", "owner"), scope()
    )
    service.raise_alert(
        OperationsAlert("alert-1", "tenant-1", "w1", "high", "risk", "risk", "review"),
        scope(),
    )
    service.open_incident(
        OperationsIncident(
            "incident-1",
            "tenant-1",
            "w1",
            "Restriction",
            "",
            "p1",
            "high",
            "risk",
            "owner",
        ),
        scope(),
    )
    overview = service.overview(scope())
    assert overview["total_accounts"] == 5
    assert overview["queued_tasks"] == 1
    assert overview["risk_alerts"] == 1
    assert overview["open_incidents"] == 1
    assert overview["unified_status"]["accounts_status"] == "degraded"
    dashboard = service.dashboard(scope())
    assert "Operations Overview" in dashboard["sections"]
    assert 0 <= dashboard["health"]["composite_platform_health"] <= 100


def test_actions_require_rbac_audit_and_high_risk_approval() -> None:
    port = Port()
    service = TikTokOperationsCommandCenter({"accounts": port})
    service.execute_action(
        ActionKind.PAUSE_ACCOUNT,
        "account://1",
        "accounts",
        "operator request",
        "corr-1",
        scope(),
    )
    assert port.calls == [("pause_account", "account://1")]
    assert service.audit[-1].correlation_id == "corr-1"
    with pytest.raises(PermissionError):
        service.execute_action(
            ActionKind.RESUME_ACCOUNT,
            "account://1",
            "accounts",
            "reviewed",
            "corr-2",
            scope(),
        )
    approval = Approval(
        "approval-1",
        "tenant-1",
        "w1",
        ActionKind.RESUME_ACCOUNT,
        "account://1",
        "reviewer",
        utcnow() + timedelta(hours=1),
    )
    service.approve(approval, scope())
    service.execute_action(
        ActionKind.RESUME_ACCOUNT,
        "account://1",
        "accounts",
        "reviewed",
        "corr-2",
        scope(),
    )
    assert ActionKind.RESUME_ACCOUNT in HIGH_RISK_ACTIONS


def test_kill_switch_and_recovery_stop_on_restriction_or_challenge() -> None:
    service = TikTokOperationsCommandCenter()
    service.approve(
        Approval(
            "kill-approval",
            "tenant-1",
            "w1",
            ActionKind.KILL_SWITCH,
            "workspace://w1",
            "reviewer",
            utcnow() + timedelta(hours=1),
        ),
        scope(),
    )
    service.execute_action(
        ActionKind.KILL_SWITCH,
        "workspace://w1",
        "risk",
        "incident",
        "corr-kill",
        scope(),
    )
    with pytest.raises(PermissionError):
        service.execute_action(
            ActionKind.PAUSE_ACCOUNT, "account://1", "accounts", "test", "corr", scope()
        )
    request = RecoveryRequest(
        "recovery-1",
        "tenant-1",
        "w1",
        "account",
        "account://1",
        "recovery://1",
        restriction_active=True,
    )
    result = service.recover(request, scope())
    assert result.attempts == 0
    assert result.outcome == "stopped_restriction_or_challenge"


def test_alert_acknowledgement_contract_api_and_metrics() -> None:
    service = TikTokOperationsCommandCenter()
    alert = service.raise_alert(
        OperationsAlert("a1", "tenant-1", "w1", "medium", "health", "browser", "down"),
        scope(),
    )
    alert.status = AlertStatus.ACKNOWLEDGED
    alert.acknowledgement = "operator"

    class App:
        def __init__(self) -> None:
            self.routes: dict[str, Any] = {}

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            self.routes[path] = endpoint

    app = App()
    register_operations_center_routes(app, service)
    assert set(ROUTES).issubset(app.routes)
    assert "/tiktok/operations/dashboard" in app.routes
    assert "/tiktok/operations/metrics" in app.routes
    assert all(name in service.metrics.render_prometheus() for name in METRIC_NAMES)


def test_only_tiktok_modules_and_safe_actions_are_exposed() -> None:
    values = {item.value for item in ActionKind}
    assert "captcha_bypass" not in values
    assert "restriction_circumvention" not in values
    assert "security_bypass" not in values
