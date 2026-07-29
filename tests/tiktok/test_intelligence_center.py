import pytest

from tiktok.intelligence_center import (
    IntelligenceContext,
    IntelligenceProfile,
    RecommendationPriority,
    TikTokAutonomousIntelligenceCenter,
)
from tiktok.intelligence_center.adapters import (
    INTEGRATION_MODULES,
    ReferenceOnlyIntelligencePort,
)
from tiktok.intelligence_center.api import ROUTES, register_intelligence_routes
from tiktok.intelligence_center.metrics import METRIC_NAMES


def context(workspace: str = "workspace") -> IntelligenceContext:
    return IntelligenceContext(
        "tenant",
        workspace,
        "analyst",
        frozenset({"tiktok:intelligence:admin"}),
    )


def profile(workspace: str = "workspace") -> IntelligenceProfile:
    return IntelligenceProfile(
        "profile",
        "Autonomous Intelligence",
        "Read-only cross-module intelligence.",
        "tenant",
        workspace,
        "analyst",
        ("governance_center", "mission_engine", "analytics_center"),
    )


def test_reasoning_is_evidence_backed_read_only_and_scoped() -> None:
    service = TikTokAutonomousIntelligenceCenter()
    service.create_profile(profile(), context())
    result = service.reason(
        "reasoning",
        "profile",
        "What requires review?",
        context(),
        confidence=0.8,
        assumptions=("Module snapshots are current.",),
    )
    assert len(result.evidence) == 3
    assert all(item.integrity_reference for item in result.evidence)
    assert not hasattr(ReferenceOnlyIntelligencePort("x"), "execute")
    with pytest.raises(PermissionError):
        service.aggregate_context("profile", "subject", context("other"))


def test_prediction_recommendation_analytics_and_security() -> None:
    service = TikTokAutonomousIntelligenceCenter()
    service.create_profile(profile(), context())
    service.reason("r", "profile", "trend", context(), confidence=0.7)
    recommendation = service.recommend(
        "rec",
        "r",
        "Review trend",
        "Evidence indicates a review is useful.",
        RecommendationPriority.MEDIUM,
        context(),
        confidence=0.6,
    )
    assert recommendation.advisory_only
    assert recommendation.requires_governance_approval
    prediction = service.predict(
        "pred",
        "r",
        "trend",
        "stable",
        3600,
        context(),
        confidence=0.6,
        assumptions=("No material input change.",),
    )
    assert prediction.horizon_seconds == 3600
    assert service.analytics(context())["recommendations_total"] == 1
    with pytest.raises(ValueError, match="Secrets"):
        unsafe = profile()
        unsafe.id = "unsafe"
        unsafe.metadata = {"token": "forbidden"}
        service.create_profile(unsafe, context())


def test_integrations_api_dashboard_and_metrics() -> None:
    assert {"governance_center", "mission_engine", "local_runtime"} <= set(
        INTEGRATION_MODULES
    )

    class App:
        def __init__(self) -> None:
            self.paths: list[str] = []

        def add_api_route(self, path: str, endpoint: object, **kwargs: object) -> None:
            self.paths.append(path)

    service = TikTokAutonomousIntelligenceCenter()
    service.create_profile(profile(), context())
    dashboard = service.dashboard(context())
    assert dashboard["sections"] == [
        "intelligence_overview",
        "reasoning",
        "predictions",
        "recommendations",
        "evidence",
        "analytics",
        "history",
    ]
    assert dashboard["intelligence_overview"]["direct_execution"] is False
    assert all(name in service.metrics.render_prometheus() for name in METRIC_NAMES)
    app = App()
    register_intelligence_routes(app, service)
    assert set(ROUTES).issubset(app.paths)
