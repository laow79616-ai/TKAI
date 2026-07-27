from datetime import timedelta

import pytest

from operations_platform import (
    METRICS,
    CapacitySnapshot,
    HealthStatus,
    MaintenanceWindow,
    OperationsCenter,
    OperationsPlatform,
    OperationsScope,
    Severity,
    utcnow,
)
from operations_platform.dashboard import SECTIONS


def scopes() -> tuple[OperationsScope, OperationsScope, OperationsScope]:
    permissions = frozenset(
        {"operations:read", "operations:write", "operations:execute"}
    )
    return (
        OperationsScope("tenant-a", "workspace-a", "operator", permissions),
        OperationsScope("tenant-b", "workspace-a", "operator", permissions),
        OperationsScope("tenant-a", "workspace-a", "viewer"),
    )


def configured() -> tuple[OperationsPlatform, OperationsScope]:
    platform = OperationsPlatform()
    scope, _, _ = scopes()
    platform.create_center(
        OperationsCenter(
            "center-a",
            "Production Operations",
            "Enterprise AI production control plane",
            "platform-team",
            scope.tenant,
            scope.workspace,
            metadata={"region": "primary"},
        ),
        scope,
    )
    return platform, scope


def test_operations_center_isolation_rbac_and_audit() -> None:
    platform, scope = configured()
    _, foreign, viewer = scopes()
    assert platform.list_centers(scope)[0].owner == "platform-team"
    assert platform.list_centers(foreign) == []
    with pytest.raises(PermissionError, match="RBAC"):
        platform.create_center(
            OperationsCenter("x", "X", "X", "x", viewer.tenant, viewer.workspace),
            viewer,
        )
    with pytest.raises(PermissionError, match="Cross-scope"):
        platform.create_center(
            OperationsCenter("x", "X", "X", "x", foreign.tenant, foreign.workspace),
            scope,
        )
    assert platform.audit[-1].action == "operations.center.create"


def test_all_health_components_and_metrics() -> None:
    platform, scope = configured()
    for component in sorted(platform.HEALTH_COMPONENTS):
        result = platform.check_health(
            component, f"{component}-a", HealthStatus.HEALTHY, scope
        )
        assert result.to_dict()["status"] == "healthy"
    assert platform.metrics.snapshot()["health_checks_total"] == 7
    with pytest.raises(ValueError):
        platform.check_health("unknown", "x", HealthStatus.UNKNOWN, scope)


def test_maintenance_approval_and_lifecycle_actions() -> None:
    platform, scope = configured()
    start = utcnow()
    for index, action in enumerate(("drain", "pause", "resume")):
        platform.schedule_maintenance(
            MaintenanceWindow(
                f"window-{index}",
                scope.tenant,
                scope.workspace,
                start,
                start + timedelta(hours=1),
                action,
            ),
            scope,
        )
    with pytest.raises(PermissionError, match="Approval"):
        platform.schedule_maintenance(
            MaintenanceWindow(
                "upgrade",
                scope.tenant,
                scope.workspace,
                start,
                start + timedelta(hours=1),
                "upgrade",
            ),
            scope,
        )
    assert (
        platform.schedule_maintenance(
            MaintenanceWindow(
                "rollback",
                scope.tenant,
                scope.workspace,
                start,
                start + timedelta(hours=1),
                "rollback",
                approval_id="approval-1",
            ),
            scope,
        ).action
        == "rollback"
    )


def test_backup_restore_preview_approval_validation_and_metrics() -> None:
    platform, scope = configured()
    backup = platform.create_backup(
        "backup-a",
        tuple(sorted(platform.BACKUP_CATEGORIES)),
        scope,
        schedule="0 2 * * *",
        retention_days=90,
    )
    assert backup.checksum
    preview = platform.restore(backup.id, scope, preview=True)
    assert preview.result["preview"]
    with pytest.raises(PermissionError, match="Approval"):
        platform.restore(backup.id, scope)
    restored = platform.restore(backup.id, scope, approval_id="approval-2")
    assert restored.result["verification"] == "passed"
    assert restored.result["rollback"] == "available"
    assert platform.metrics.snapshot()["backup_total"] == 1
    assert platform.metrics.snapshot()["restore_total"] == 1


def test_capacity_forecast_alert_automation_and_diagnostics() -> None:
    platform, scope = configured()
    snapshot = platform.record_capacity(
        CapacitySnapshot(
            scope.tenant,
            scope.workspace,
            90,
            60,
            50,
            15000,
            12,
            8,
            {"cpu_30d": 94.0},
        ),
        scope,
    )
    assert snapshot.forecast["cpu_30d"] == 94
    assert platform.metrics.snapshot()["capacity_alerts_total"] == 1
    for kind in sorted(platform.AUTOMATION_KINDS):
        platform.schedule_automation(kind, kind, {"schedule": "daily"}, scope)
    diagnostics = platform.run_diagnostics(
        (
            "health_checks",
            "dependency_graph",
            "configuration_validation",
            "performance_analysis",
            "root_cause_reference",
        ),
        scope,
    )
    assert set(diagnostics.result) == set(diagnostics.payload["checks"])


def test_logs_events_notifications_reports_dashboard_and_metrics() -> None:
    platform, scope = configured()
    entry = platform.add_log(
        "request failed token=top-secret password=hunter2",
        "orchestrator",
        "correlation-a",
        scope,
    )
    assert "top-secret" not in entry["message"]
    assert "hunter2" not in entry["message"]
    assert platform.query_logs(scope, correlation_id="correlation-a") == [entry]
    platform.record_event(
        "application.upgraded", Severity.INFO, "applications", scope, "completed"
    )
    failed = platform.notify(
        "webhook",
        "https://secret.example/hook",
        scope,
        escalation="on-call",
        sender=lambda _: False,
        retries=2,
    )
    assert failed.status == "escalated"
    assert failed.attempts == 2
    assert failed.to_dict()["destination"] == "[REDACTED]"
    for report_type in ("health", "capacity", "usage", "availability", "operations"):
        assert platform.report(report_type, scope)["type"] == report_type
    dashboard = platform.dashboard(scope)
    assert set(SECTIONS) <= dashboard.keys()
    assert set(dashboard["metrics"]) == set(METRICS)
    assert all(metric in platform.metrics.render_prometheus() for metric in METRICS)
