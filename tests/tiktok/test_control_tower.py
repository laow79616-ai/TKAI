"""Mock-only tests for the Enterprise TikTok AI Control Tower."""

from __future__ import annotations

from typing import Any

import pytest

from tiktok.control_tower import (
    ControlTowerScope,
    MockControlTowerProvider,
    TikTokAIControlTower,
)
from tiktok.control_tower.api import ROUTES, register_control_tower_routes
from tiktok.control_tower.metrics import METRIC_NAMES
from tiktok.control_tower.models import CONTROL_TOWER_MODULES, DASHBOARD_SECTIONS


def scope(
    workspace: str = "workspace",
    permissions: frozenset[str] = frozenset({"tiktok:control-tower:admin"}),
) -> ControlTowerScope:
    return ControlTowerScope("tenant", workspace, "operator", permissions)


def tower() -> TikTokAIControlTower:
    return TikTokAIControlTower(MockControlTowerProvider())


def test_overview_aggregates_global_health_and_required_statuses() -> None:
    overview = tower().overview(scope())
    assert overview["global_health"] == "healthy"
    assert overview["platform_status"]["healthy"] == len(CONTROL_TOWER_MODULES)
    assert set(overview) >= {
        "unified_overview",
        "live_runtime",
        "resource_utilization",
        "workflow_status",
        "execution_status",
        "automation_status",
        "risk_status",
        "recovery_status",
        "analytics_summary",
    }


def test_dashboard_and_topology_cover_every_required_section() -> None:
    service = tower()
    dashboard = service.dashboard(scope())
    topology = service.topology(scope())
    assert dashboard["sections"] == list(DASHBOARD_SECTIONS)
    assert len(topology["nodes"]) == len(CONTROL_TOWER_MODULES)
    assert len(topology["edges"]) == len(CONTROL_TOWER_MODULES)
    assert all(edge["mode"] == "read-only" for edge in topology["edges"])


def test_runtime_resources_recovery_and_analytics_are_module_projections() -> None:
    service = tower()
    assert service.module("runtime", scope())["module"] == "runtime"
    assert service.module("resources", scope())["summary"]["capacity_percent"] == 25
    assert service.module("recovery", scope())["status"] == "operational"
    assert service.module("analytics", scope())["health"] == "healthy"
    with pytest.raises(ValueError, match="Unknown"):
        service.module("unrelated-platform", scope())


def test_alert_activity_audit_encryption_and_workspace_isolation() -> None:
    service = tower()
    alert = service.create_alert(
        scope(), "risk", "warning", "Bounded review required", "risk://raw/1"
    )
    service.record_activity(
        scope(), "overview.read", "analytics", "operator viewed summary"
    )
    assert alert.reference.startswith("sealed-ref://")
    assert "risk://raw/1" not in alert.reference
    assert len(service.scoped_alerts(scope())) == 1
    assert len(service.scoped_alerts(scope("other"))) == 0
    assert len(service.scoped_activity(scope())) == 1
    assert len(service.scoped_activity(scope("other"))) == 0


def test_rbac_and_no_secrets_in_logs() -> None:
    service = tower()
    reader = scope(
        permissions=frozenset({"tiktok:control-tower:read"}),
    )
    assert service.overview(reader)["global_health"] == "healthy"
    with pytest.raises(PermissionError, match="alert"):
        service.create_alert(reader, "risk", "info", "review", "risk://1")
    with pytest.raises(ValueError, match="Secrets"):
        service.record_activity(scope(), "audit", "runtime", "token=forbidden")


def test_api_contract_and_route_registration() -> None:
    class FakeApp:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            self.paths.append(path)

    app = FakeApp()
    register_control_tower_routes(app, tower())
    assert set(ROUTES).issubset(app.paths)
    assert "/tiktok/control-tower/dashboard" in app.paths
    assert "/tiktok/control-tower/metrics" in app.paths


def test_metrics_contract() -> None:
    service = tower()
    service.overview(scope())
    rendered = service.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
    assert service.metrics.values["tiktok_control_tower_health"] == 1


def test_regression_scope_is_tiktok_only_and_safe() -> None:
    names = " ".join(CONTROL_TOWER_MODULES)
    assert "telegram" not in names
    assert "whatsapp" not in names
    assert "facebook" not in names
    assert "instagram" not in names
    assert "discord" not in names
    assert "billing" not in names
    assert "subscription" not in names
    assert len(ROUTES) == 9
