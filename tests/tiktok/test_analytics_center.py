from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from tiktok.analytics_center import (
    KPI,
    AnalyticsScope,
    AnalyticsStatus,
    AnalyticsWorkspace,
    DataPoint,
    ExportFormat,
    HistorySnapshot,
    Insight,
    KPIKind,
    Period,
    Report,
    ReportType,
    TikTokAIAnalyticsCenter,
)
from tiktok.analytics_center.api import ROUTES, register_analytics_center_routes
from tiktok.analytics_center.metrics import METRIC_NAMES
from tiktok.analytics_center.models import utcnow


def scope(workspace: str = "w1") -> AnalyticsScope:
    return AnalyticsScope(
        "tenant-1", workspace, "analyst", frozenset({"tiktok:analytics:admin"})
    )


def test_workspace_lifecycle_rbac_isolation_and_secret_validation() -> None:
    service = TikTokAIAnalyticsCenter()
    item = service.create_workspace(
        AnalyticsWorkspace("a1", "Analytics", "", "tenant-1", "w1", "owner"),
        scope(),
    )
    assert service.transition(item.id, AnalyticsStatus.GENERATING, scope()).version == 2
    assert service.transition(item.id, AnalyticsStatus.READY, scope()).version == 3
    with pytest.raises(PermissionError):
        service.transition(item.id, AnalyticsStatus.ARCHIVED, scope("other"))
    with pytest.raises(ValueError):
        service.create_workspace(
            AnalyticsWorkspace(
                "bad",
                "Bad",
                "",
                "tenant-1",
                "w1",
                "owner",
                metadata={"token": "plaintext"},
            ),
            scope(),
        )


def test_reports_kpis_trends_forecast_history_insights_and_dashboard() -> None:
    service = TikTokAIAnalyticsCenter()
    report = service.generate_report(
        Report(
            "r1",
            "tenant-1",
            "w1",
            "Account health",
            ReportType.ACCOUNTS,
            "dataset://accounts",
            "owner",
        ),
        scope(),
    )
    assert report.status is AnalyticsStatus.READY
    kpi = service.record_kpi(
        KPI(
            "k1",
            "tenant-1",
            "w1",
            KPIKind.ACCOUNT_HEALTH,
            98.5,
            "percent",
            ["metric://account-health"],
        ),
        scope(),
    )
    assert kpi.value == 98.5
    points = [
        DataPoint(utcnow() - timedelta(days=2), 10),
        DataPoint(utcnow() - timedelta(days=1), 12),
        DataPoint(utcnow(), 14),
    ]
    trend = service.analyze_trend("t1", "success", Period.DAILY, points, scope())
    assert trend.growth == 40
    forecast = service.create_forecast("f1", "success", points, 3, scope())
    assert len(forecast.historical_projection) == 3
    assert 0 <= forecast.confidence <= 1
    snapshot = service.snapshot(
        HistorySnapshot("h1", "tenant-1", "w1", {"success": 14}), scope()
    )
    assert service.archive_snapshot(snapshot.id, True, scope()).archived
    assert not service.archive_snapshot(snapshot.id, False, scope()).archived
    insight = service.create_insight(
        Insight(
            "i1",
            "tenant-1",
            "w1",
            "anomaly://detector-1",
            "Success is increasing",
            ["Maintain capacity"],
            ["Two-day growth"],
            ["trend://t1"],
        ),
        scope(),
    )
    assert insight.evidence_references == ["trend://t1"]
    assert service.dashboard(scope())["sections"] == [
        "Overview",
        "KPIs",
        "Reports",
        "Trends",
        "Forecast",
        "Insights",
        "History",
        "Exports",
    ]


def test_exports_require_authorization_are_audited_and_contain_no_secrets() -> None:
    service = TikTokAIAnalyticsCenter()
    service.generate_report(
        Report(
            "r1",
            "tenant-1",
            "w1",
            "Workflow",
            ReportType.WORKFLOW,
            "dataset://workflow",
            "owner",
        ),
        scope(),
    )
    record, content = service.export_report("r1", ExportFormat.CSV, "e1", scope())
    assert record.artifact_reference == "analytics-export://e1"
    assert "dataset://workflow" in content
    _, json_content = service.export_report("r1", ExportFormat.JSON, "e2", scope())
    assert '"report_type": "workflow"' in json_content
    denied = AnalyticsScope("tenant-1", "w1", "reader")
    with pytest.raises(PermissionError):
        service.export_report("r1", ExportFormat.JSON, "e3", denied)
    assert service.audit[-1].action == "report.exported"


def test_module_integrations_are_read_only_and_tiktok_only() -> None:
    class Port:
        def __init__(self) -> None:
            self.calls = 0

        def metrics(self, analytics_scope: AnalyticsScope) -> dict[str, float]:
            self.calls += 1
            return {"availability": 99}

    port = Port()
    service = TikTokAIAnalyticsCenter({"accounts": port})
    overview = service.overview(scope())
    assert overview["modules"]["accounts"]["availability"] == 99
    assert port.calls == 1
    assert not any(
        platform in service.ports
        for platform in ("telegram", "whatsapp", "facebook", "instagram", "discord")
    )


def test_api_metrics_validation_and_mock_only_contract() -> None:
    service = TikTokAIAnalyticsCenter()

    class App:
        def __init__(self) -> None:
            self.routes: dict[str, Any] = {}

        def add_api_route(self, path: str, endpoint: Any, **kwargs: Any) -> None:
            self.routes[path] = endpoint

    app = App()
    register_analytics_center_routes(app, service)
    assert set(ROUTES).issubset(app.routes)
    assert "/tiktok/analytics/dashboard" in app.routes
    assert "/tiktok/analytics/metrics" in app.routes
    assert all(name in service.metrics.render_prometheus() for name in METRIC_NAMES)
    with pytest.raises(ValueError):
        service.analyze_trend("bad", "metric", Period.HOURLY, [], scope())
    with pytest.raises(ValueError):
        service.snapshot(
            HistorySnapshot("bad-history", "tenant-1", "w1", {}, retention_days=0),
            scope(),
        )
