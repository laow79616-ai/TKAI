"""Offline tests for the Enterprise TikTok Predictive Analytics Center."""

from datetime import datetime, timedelta, timezone

import pytest

from tiktok.predictive_analytics import (
    CapacityForecast,
    ConfidenceEstimate,
    Forecast,
    ForecastEvaluation,
    PredictiveContext,
    PredictiveProfile,
    PredictiveRecommendation,
    RiskForecast,
    Scenario,
    TikTokPredictiveAnalyticsCenter,
    TrendAnalysis,
)
from tiktok.predictive_analytics.adapters import (
    PREDICTIVE_SOURCES,
    ReferenceOnlyPredictiveSource,
)
from tiktok.predictive_analytics.api import ROUTES, register_predictive_routes
from tiktok.predictive_analytics.metrics import METRIC_NAMES

NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def context(
    workspace: str = "workspace",
    permissions: frozenset[str] = frozenset({"tiktok:predictive:admin"}),
) -> PredictiveContext:
    return PredictiveContext("tenant", workspace, "analyst", permissions)


def profile(workspace: str = "workspace") -> PredictiveProfile:
    return PredictiveProfile(
        "profile",
        "Engagement outlook",
        "tenant",
        workspace,
        "analyst",
        PREDICTIVE_SOURCES,
        30,
        NOW - timedelta(days=90),
        NOW,
        "qualified_engagement",
    )


def forecast(workspace: str = "workspace") -> Forecast:
    return Forecast(
        "forecast",
        "profile",
        "tenant",
        workspace,
        "qualified_engagement",
        14,
        120.0,
        100.0,
        140.0,
        0.8,
        "bounded_linear_trend",
        NOW,
        ("analytics://history/1",),
        ("Historical reporting remains comparable.",),
    )


def configured_service() -> TikTokPredictiveAnalyticsCenter:
    service = TikTokPredictiveAnalyticsCenter()
    service.create_profile(profile(), context())
    service.generate_forecast(forecast(), context())
    return service


def test_approved_sources_are_bounded_scoped_read_only_and_mocked() -> None:
    service = TikTokPredictiveAnalyticsCenter(max_results=25)
    service.create_profile(profile(), context())
    rows = service.collect("profile", context())
    assert set(rows) == set(PREDICTIVE_SOURCES)
    assert all(
        row["read_only"]
        and row["reference_only"]
        and not row["execution"]
        and not row["publishing"]
        for values in rows.values()
        for row in values
    )
    adapter = ReferenceOnlyPredictiveSource("knowledge_evolution")
    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "publish")
    assert not hasattr(adapter, "configure")


def test_profiles_enforce_bounds_rbac_scope_and_no_secrets() -> None:
    service = TikTokPredictiveAnalyticsCenter(max_history_days=90)
    service.create_profile(profile(), context())
    with pytest.raises(PermissionError, match="RBAC"):
        service.analytics(context(permissions=frozenset()))
    with pytest.raises(PermissionError, match="Cross-tenant"):
        service.collect("profile", context("other"))
    unsafe = PredictiveProfile(
        "unsafe",
        "Unsafe",
        "tenant",
        "workspace",
        "analyst",
        ("analytics_center",),
        7,
        NOW - timedelta(days=7),
        NOW,
        "views",
        {"token": "forbidden"},
    )
    with pytest.raises(ValueError, match="Secrets"):
        service.create_profile(unsafe, context())


def test_trends_reject_unsupported_causal_claims() -> None:
    service = TikTokPredictiveAnalyticsCenter()
    service.create_profile(profile(), context())
    trend = TrendAnalysis(
        "trend",
        "profile",
        "tenant",
        "workspace",
        "qualified_engagement",
        "increasing",
        1.5,
        30,
        30,
        ("analytics://trend/1",),
        "The historical series increased during the selected window.",
    )
    service.analyze_trend(trend, context())
    with pytest.raises(ValueError, match="causal"):
        service.analyze_trend(
            TrendAnalysis(
                "causal",
                "profile",
                "tenant",
                "workspace",
                "views",
                "increasing",
                2.0,
                10,
                10,
                ("analytics://trend/2",),
                "Unsupported cause.",
                causal_claim=True,
            ),
            context(),
        )


def test_forecasts_are_bounded_explainable_and_advisory() -> None:
    service = configured_service()
    result = service.forecasts["forecast"]
    assert result.lower_bound <= result.predicted_value <= result.upper_bound
    assert result.assumptions
    assert result.advisory_only
    assert not result.direct_execution
    invalid = Forecast(
        "invalid",
        "profile",
        "tenant",
        "workspace",
        "qualified_engagement",
        14,
        120,
        100,
        140,
        0.8,
        "bounded_linear_trend",
        NOW,
        ("analytics://history/2",),
        ("Comparable history.",),
        direct_execution=True,
    )
    with pytest.raises(ValueError, match="advisory"):
        service.generate_forecast(invalid, context())


def test_scenario_capacity_risk_and_confidence_forecasts() -> None:
    service = configured_service()
    service.compare_scenario(
        Scenario(
            "scenario",
            "profile",
            "tenant",
            "workspace",
            "high demand",
            ("Demand rises by ten percent.",),
            132,
            12,
            0.4,
            0.75,
            "A sensitivity scenario, not a causal prediction.",
        ),
        context(),
    )
    service.forecast_capacity(
        CapacityForecast(
            "capacity",
            "profile",
            "tenant",
            "workspace",
            "review_hours",
            14,
            80,
            60,
            20,
            0.7,
            ("operations-planner://capacity/1",),
        ),
        context(),
    )
    service.forecast_risk(
        RiskForecast(
            "risk",
            "profile",
            "tenant",
            "workspace",
            "operational_load",
            14,
            0.3,
            0.45,
            "increasing",
            0.7,
            ("risk-control://trend/1",),
            "risk-control://mitigation/1",
        ),
        context(),
    )
    service.estimate_confidence(
        ConfidenceEstimate(
            "confidence",
            "forecast",
            "tenant",
            "workspace",
            0.78,
            90,
            0.8,
            0.75,
            0.1,
            "Confidence reflects sample size, data quality, and calibration.",
        ),
        context(),
    )
    assert service.analytics(context())["scenarios_total"] == 1
    assert service.analytics(context())["capacity_forecasts_total"] == 1
    assert service.analytics(context())["risk_forecasts_total"] == 1


def test_recommendations_and_evaluations_remain_reference_only() -> None:
    service = configured_service()
    recommendation = service.recommend(
        PredictiveRecommendation(
            "recommendation",
            "profile",
            "tenant",
            "workspace",
            "capacity",
            "Review capacity assumptions with an operator.",
            "The advisory forecast range overlaps available capacity.",
            ("capacity://forecast/1",),
            0.72,
        ),
        context(),
    )
    assert recommendation.advisory_only
    assert not recommendation.automatic_decision
    assert not recommendation.runtime_change
    service.evaluate_forecast(
        ForecastEvaluation(
            "evaluation",
            "forecast",
            "tenant",
            "workspace",
            "analytics://actual/1",
            125,
            5,
            0.04,
            True,
            NOW + timedelta(days=14),
        ),
        context(),
    )
    analytics = service.analytics(context())
    assert analytics["evaluations_total"] == 1
    assert analytics["mean_absolute_error"] == 5


def test_dashboard_api_metrics_history_and_registry_contract() -> None:
    class App:
        def __init__(self) -> None:
            self.routes: list[tuple[str, list[str]]] = []

        def add_api_route(self, path: str, endpoint: object, **kwargs: object) -> None:
            self.routes.append((path, list(kwargs["methods"])))

    service = configured_service()
    dashboard = service.dashboard(context())
    assert dashboard["forecast_overview"]["advisory_only"]
    assert not dashboard["forecast_overview"]["direct_execution"]
    assert not dashboard["forecast_overview"]["restriction_bypass"]
    assert dashboard["sections"] == (
        "Forecast Overview",
        "Trend Analysis",
        "Scenario Comparison",
        "Capacity Forecast",
        "Risk Forecast",
        "Confidence",
        "Recommendations",
        "Analytics",
        "History",
    )
    assert service.get_history(context())
    assert all(name in service.metrics.render_prometheus() for name in METRIC_NAMES)
    app = App()
    register_predictive_routes(app, service)
    assert set(ROUTES).issubset(path for path, _ in app.routes)
    assert all(methods == ["GET"] for _, methods in app.routes)
