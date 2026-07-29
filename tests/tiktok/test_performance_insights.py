"""Offline validation for the TikTok Performance Insights Center."""

from datetime import datetime, timedelta, timezone

import pytest

from tiktok.performance_insights.adapters import INTEGRATION_MODULES
from tiktok.performance_insights.api import RESOURCES, ROUTES
from tiktok.performance_insights.metrics import METRIC_NAMES
from tiktok.performance_insights.models import (
    Anomaly,
    AnomalyKind,
    Dataset,
    Forecast,
    ForecastKind,
    Insight,
    Metric,
    MetricKind,
    PerformanceProfile,
    PerformanceScope,
    PerformanceStatus,
    Recommendation,
    RecommendationKind,
    RequestScope,
    TimeRange,
    Trend,
    TrendPeriod,
)
from tiktok.performance_insights.service import TikTokPerformanceInsightsCenter

NOW = datetime(2026, 7, 28, tzinfo=timezone.utc)
RANGE = TimeRange(NOW - timedelta(days=7), NOW)


def scope(workspace: str = "workspace") -> RequestScope:
    return RequestScope(
        "tenant",
        workspace,
        "operator",
        frozenset({"tiktok:performance:admin"}),
    )


def profile() -> PerformanceProfile:
    return PerformanceProfile(
        "profile-1",
        "Weekly overview",
        "Explain performance",
        "tenant",
        "workspace",
        "operator",
        PerformanceScope.PLATFORM,
        RANGE,
    )


def test_lifecycle_isolation_history_and_bounded_queries() -> None:
    center = TikTokPerformanceInsightsCenter()
    center.create_profile(profile(), scope())
    for status in (
        PerformanceStatus.COLLECTING,
        PerformanceStatus.ANALYZING,
        PerformanceStatus.READY,
        PerformanceStatus.REVIEW,
        PerformanceStatus.APPROVED,
        PerformanceStatus.ARCHIVED,
        PerformanceStatus.DELETED,
    ):
        center.transition("profile-1", status, scope())
    assert len(center.history(scope())["profile_history"]) == 8
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.create_profile(profile(), scope("other"))
    with pytest.raises(ValueError, match="500"):
        center.scoped_values(center.profiles.values(), scope(), 501)
    with pytest.raises(ValueError, match="366"):
        TimeRange(NOW - timedelta(days=367), NOW).validate()


def test_dataset_integrity_metric_dimensions_and_read_only_integrations() -> None:
    center = TikTokPerformanceInsightsCenter()
    center.create_profile(profile(), scope())
    center.add_dataset(
        Dataset(
            "dataset-1",
            "profile-1",
            "tenant",
            "workspace",
            "growth_center",
            "ref://growth/snapshot",
            "ref://schema/performance",
            RANGE,
            "daily",
            60,
            1,
            "verified",
            "encrypted://datasets/1",
        ),
        scope(),
    )
    center.evaluate_metric(
        Metric(
            "metric-1",
            "profile-1",
            "tenant",
            "workspace",
            MetricKind.RUNTIME_AVAILABILITY,
            0.99,
            "ratio",
            {"workspace": "workspace", "time": "daily"},
            ["ref://runtime/evidence/1"],
        ),
        scope(),
    )
    snapshots = center.integration_snapshot(scope(), RANGE, 50)
    assert tuple(snapshots) == INTEGRATION_MODULES
    assert all(item["read_only"] for item in snapshots.values())
    bad = Metric(
        "bad",
        "profile-1",
        "tenant",
        "workspace",
        MetricKind.CUSTOM_BOUNDED,
        1,
        "count",
        {"unknown": "x"},
        ["ref://x"],
    )
    with pytest.raises(ValueError, match="dimension"):
        center.evaluate_metric(bad, scope())


def test_explainable_advisory_outputs_and_safety() -> None:
    center = TikTokPerformanceInsightsCenter()
    center.create_profile(profile(), scope())
    center.analyze_trend(
        Trend(
            "trend-1",
            "profile-1",
            "tenant",
            "workspace",
            TrendPeriod.DAILY,
            0.1,
            0,
            "ref://change/1",
            0.8,
            ["ref://metric/1"],
        ),
        scope(),
    )
    center.add_anomaly(
        Anomaly(
            "anomaly-1",
            "profile-1",
            "tenant",
            "workspace",
            AnomalyKind.LATENCY_SPIKE,
            "medium",
            "ref://evidence/latency",
            "Queue latency exceeded its historical baseline",
        ),
        scope(),
    )
    center.forecast(
        Forecast(
            "forecast-1",
            "profile-1",
            "tenant",
            "workspace",
            ForecastKind.CAPACITY,
            RANGE,
            12,
            0.7,
            ["ref://capacity/1"],
        ),
        scope(),
    )
    center.add_insight(
        Insight(
            "insight-1",
            "profile-1",
            "tenant",
            "workspace",
            "Review queue increased",
            "Capacity is below its rolling baseline",
            PerformanceScope.CONTENT_PIPELINE,
            "medium",
            0.78,
            ["ref://pipeline/evidence/1"],
            trend_reference="ref://trend/1",
            recommended_review="Review staffing and schedule assumptions",
        ),
        scope(),
    )
    center.recommend(
        Recommendation(
            "rec-1",
            "profile-1",
            "tenant",
            "workspace",
            RecommendationKind.SCHEDULE,
            "Review the publishing schedule",
            "Queue evidence suggests a bounded schedule review",
            ["ref://insight/1"],
        ),
        scope(),
    )
    unsafe = Recommendation(
        "bad",
        "profile-1",
        "tenant",
        "workspace",
        RecommendationKind.OPERATIONAL,
        "CAPTCHA bypass",
        "unsafe",
        ["ref://evidence/1"],
    )
    with pytest.raises(ValueError, match="Unsafe"):
        center.recommend(unsafe, scope())
    assert center.dashboard(scope())["direct_execution"] is False


def test_api_dashboard_analytics_and_metrics_exposure() -> None:
    center = TikTokPerformanceInsightsCenter()
    center.create_profile(profile(), scope())
    assert len(ROUTES) == len(RESOURCES) == 14
    assert len(center.dashboard(scope())["sections"]) == 15
    assert center.analytics(scope())["profiles_total"] == 1
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
