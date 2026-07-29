from __future__ import annotations

import pytest

from tiktok.learning_center import (
    HistoricalOutcome,
    LearningContext,
    LearningProfile,
    TikTokAutonomousLearningCenter,
)
from tiktok.learning_center.adapters import (
    INTEGRATION_MODULES,
    ReferenceOnlyLearningPort,
)
from tiktok.learning_center.api import ROUTES, register_learning_routes
from tiktok.learning_center.dashboard import SECTIONS
from tiktok.learning_center.metrics import METRIC_NAMES


def context(workspace: str = "workspace") -> LearningContext:
    return LearningContext(
        "tenant",
        workspace,
        "analyst",
        frozenset({"tiktok:learning:admin"}),
    )


def outcomes() -> tuple[HistoricalOutcome, ...]:
    return (
        HistoricalOutcome("analytics_center", "campaign", "strong", 0.8, "a:1"),
        HistoricalOutcome("analytics_center", "campaign", "strong", 0.9, "a:2"),
        HistoricalOutcome("analytics_center", "campaign", "weak", 0.2, "a:3"),
    )


def service() -> TikTokAutonomousLearningCenter:
    return TikTokAutonomousLearningCenter(
        {"analytics_center": ReferenceOnlyLearningPort("analytics_center", outcomes())}
    )


def profile(workspace: str = "workspace") -> LearningProfile:
    return LearningProfile(
        "profile",
        "Historical outcomes",
        "Offline learning only.",
        "tenant",
        workspace,
        "analyst",
        ("analytics_center",),
    )


def test_historical_learning_and_pattern_discovery_are_bounded() -> None:
    center = service()
    center.create_profile(profile(), context())
    patterns = center.discover_patterns("profile", "campaign", context())
    assert len(patterns) == 1
    assert patterns[0].outcome == "strong"
    assert patterns[0].sample_size == 2
    assert patterns[0].average_score == pytest.approx(0.85)
    assert patterns[0].evidence_references == ("a:1", "a:2")
    assert not hasattr(center.modules["analytics_center"], "execute")
    assert not hasattr(center.modules["analytics_center"], "publish")


def test_lessons_recommendations_confidence_and_analytics() -> None:
    center = service()
    center.create_profile(profile(), context())
    pattern = center.discover_patterns("profile", "campaign", context())[0]
    lesson = center.extract_lesson(
        "lesson", pattern.id, "Strong outcomes recurred.", context()
    )
    recommendation = center.recommend(
        "recommendation",
        lesson.id,
        "Review the recurring conditions",
        "Two attributable outcomes support a human review.",
        context(),
        confidence=0.5,
    )
    assert recommendation.advisory_only
    assert recommendation.requires_human_review
    assert center.analytics(context())["mean_confidence"] == 0.5
    assert center.evaluate((pattern.id,), context())[
        "mean_outcome_score"
    ] == pytest.approx(0.85)
    with pytest.raises(ValueError, match="cannot exceed"):
        center.recommend(
            "bad", lesson.id, "Bad", "Overconfident", context(), confidence=0.9
        )


def test_tenant_workspace_rbac_and_secret_safety() -> None:
    center = service()
    center.create_profile(profile(), context())
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.collect_dataset("profile", "campaign", context("other"))
    with pytest.raises(PermissionError, match="RBAC"):
        center.create_profile(
            profile(),
            LearningContext("tenant", "workspace", "reader"),
        )
    unsafe = profile()
    unsafe.id = "unsafe"
    unsafe.metadata = {"token": "forbidden"}
    with pytest.raises(ValueError, match="Secrets"):
        center.create_profile(unsafe, context())
    assert all("token" not in str(record).casefold() for record in center.audit)


def test_api_dashboard_metrics_and_completed_module_integrations() -> None:
    required = {
        "intelligence_center",
        "governance_center",
        "strategy_center",
        "mission_engine",
        "analytics_center",
        "recovery_center",
        "local_runtime",
    }
    assert required <= set(INTEGRATION_MODULES)
    center = service()
    center.create_profile(profile(), context())
    dashboard = center.dashboard(context())
    assert tuple(dashboard["sections"]) == SECTIONS
    overview = dashboard["learning_overview"]
    assert overview["read_only_integrations"]
    assert not overview["direct_runtime_configuration"]
    assert not overview["direct_execution"]
    assert not overview["publishing"]
    assert not overview["restriction_bypass"]
    assert all(name in center.metrics.render_prometheus() for name in METRIC_NAMES)

    class App:
        def __init__(self) -> None:
            self.routes: dict[str, tuple[str, ...]] = {}

        def add_api_route(
            self, path: str, endpoint: object, **kwargs: object
        ) -> None:
            del endpoint
            self.routes[path] = tuple(kwargs["methods"])  # type: ignore[arg-type]

    app = App()
    register_learning_routes(app, TikTokAutonomousLearningCenter())
    assert set(ROUTES) <= set(app.routes)
    assert all(methods == ("GET",) for methods in app.routes.values())
