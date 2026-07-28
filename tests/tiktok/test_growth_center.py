"""Offline coverage for the Enterprise TikTok AI Growth Center."""

from __future__ import annotations

import pytest

from tiktok.growth_center import (
    Approval,
    GrowthGoal,
    GrowthObjective,
    GrowthOpportunity,
    GrowthProfile,
    GrowthRecommendation,
    GrowthSimulation,
    GrowthStatus,
    KPIKind,
    KPIRecord,
    RecommendationKind,
    RequestScope,
    SimulationKind,
    TrendPeriod,
    TrendRecord,
)
from tiktok.growth_center.adapters import INTEGRATION_MODULES, BoundedTestDouble
from tiktok.growth_center.api import ROUTES
from tiktok.growth_center.metrics import METRIC_NAMES
from tiktok.growth_center.service import TikTokAIGrowthCenter


def scope(workspace: str = "workspace") -> RequestScope:
    return RequestScope(
        "tenant", workspace, "operator", frozenset({"tiktok:growth:admin"})
    )


def profile() -> GrowthProfile:
    return GrowthProfile(
        "profile-1",
        "Sustainable growth",
        "tenant",
        "workspace",
        "operator",
        GrowthObjective.CONTENT_QUALITY,
    )


def recommendation() -> GrowthRecommendation:
    return GrowthRecommendation(
        "recommendation-1",
        "profile-1",
        "tenant",
        "workspace",
        RecommendationKind.CONTENT_PLANNING,
        "Improve planning mix",
        "Quality is stable and review throughput has capacity",
        "Higher consistency",
        ["ref://analytics/evidence/1"],
        0.82,
    )


def test_lifecycle_goals_kpis_trends_and_history() -> None:
    center = TikTokAIGrowthCenter()
    center.create_profile(profile(), scope())
    statuses = (
        GrowthStatus.ANALYZING,
        GrowthStatus.PROPOSED,
        GrowthStatus.REVIEW,
        GrowthStatus.APPROVED,
        GrowthStatus.TRACKING,
        GrowthStatus.COMPLETED,
        GrowthStatus.ARCHIVED,
        GrowthStatus.DELETED,
    )
    for status in statuses:
        center.transition("profile-1", status, scope())
    center.add_goal(
        GrowthGoal(
            "goal-1",
            "profile-1",
            "tenant",
            "workspace",
            GrowthObjective.CONTENT_OUTPUT,
            3,
            5,
            "items/week",
        ),
        scope(),
    )
    center.record_kpi(
        KPIRecord(
            "kpi-1",
            "profile-1",
            "tenant",
            "workspace",
            KPIKind.PIPELINE_THROUGHPUT,
            4,
            "items/week",
            "encrypted://analytics/kpi/1",
        ),
        scope(),
    )
    center.analyze_trend(
        TrendRecord(
            "trend-1",
            "profile-1",
            "tenant",
            "workspace",
            TrendPeriod.WEEKLY,
            0.7,
            0.1,
            ["ref://analytics/trend/1"],
            "Positive trend",
        ),
        scope(),
    )
    assert len(center.history(scope())["profile_versions"]) == 9
    assert center.metrics.values["tiktok_growth_goals_total"] == 1


def test_recommendations_are_advisory_and_proposals_require_approval() -> None:
    adapter = BoundedTestDouble()
    center = TikTokAIGrowthCenter(adapter, adapter)
    center.create_profile(profile(), scope())
    center.recommend(recommendation(), scope())
    with pytest.raises(PermissionError, match="approval"):
        center.create_execution_proposal("recommendation-1", scope())
    center.approve(
        Approval(
            "approval-1",
            "recommendation-1",
            "tenant",
            "workspace",
            "reviewer",
            True,
            "bounded",
        ),
        scope(),
    )
    assert (
        center.create_execution_proposal("recommendation-1", scope())
        == "ref://growth-proposal/recommendation-1"
    )
    assert adapter.proposals == ["recommendation-1"]


def test_offline_forecast_opportunity_and_integrations() -> None:
    center = TikTokAIGrowthCenter()
    center.create_profile(profile(), scope())
    center.add_opportunity(
        GrowthOpportunity(
            "opp-1",
            "profile-1",
            "tenant",
            "workspace",
            "Use review capacity",
            0.8,
            0.3,
            ["ref://pipeline/1"],
        ),
        scope(),
    )
    center.simulate(
        GrowthSimulation(
            "forecast-1",
            "profile-1",
            "tenant",
            "workspace",
            SimulationKind.FORECAST,
            {"weekly_output": 5},
            12,
            0.7,
            "ref://simulation/1",
        ),
        scope(),
    )
    assert tuple(center.integration_snapshot(scope())) == INTEGRATION_MODULES
    with pytest.raises(ValueError, match="live TikTok"):
        center.simulate(
            GrowthSimulation(
                "bad",
                "profile-1",
                "tenant",
                "workspace",
                SimulationKind.TREND,
                {},
                1,
                0.5,
                "ref://simulation/bad",
                True,
            ),
            scope(),
        )


def test_security_dashboard_api_metrics_and_analytics() -> None:
    center = TikTokAIGrowthCenter()
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.create_profile(profile(), scope("other"))
    unsafe = profile()
    unsafe.metadata = {"token": "forbidden"}
    with pytest.raises(ValueError, match="Secrets"):
        center.create_profile(unsafe, scope())
    center.create_profile(profile(), scope())
    unsafe_rec = recommendation()
    unsafe_rec.title = "CAPTCHA bypass"
    with pytest.raises(ValueError, match="Unsafe"):
        center.recommend(unsafe_rec, scope())
    assert len(ROUTES) == 6
    assert len(center.dashboard(scope())["sections"]) == 8
    assert center.analytics(scope())["growth_profiles"] == 1
    assert all(name in center.metrics.render_prometheus() for name in METRIC_NAMES)
