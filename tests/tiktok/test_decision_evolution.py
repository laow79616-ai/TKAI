"""Offline tests for the Enterprise TikTok Decision Evolution Center."""

from datetime import datetime, timedelta, timezone

import pytest

from tiktok.decision_evolution import (
    DecisionBaseline,
    DecisionComparison,
    DecisionEvolutionContext,
    DecisionEvolutionProfile,
    DecisionLesson,
    DecisionOutcome,
    DecisionPattern,
    DecisionRecord,
    DecisionReview,
    ProfileStatus,
    TikTokDecisionEvolutionCenter,
)
from tiktok.decision_evolution.adapters import (
    DECISION_SOURCES,
    ReferenceOnlyDecisionSource,
)
from tiktok.decision_evolution.api import (
    ROUTES,
    register_decision_evolution_routes,
)
from tiktok.decision_evolution.metrics import METRIC_NAMES

NOW = datetime(2026, 1, 15, tzinfo=timezone.utc)


def context(
    workspace: str = "workspace",
    permissions: frozenset[str] = frozenset(
        {"tiktok:decision-evolution:admin"}
    ),
) -> DecisionEvolutionContext:
    return DecisionEvolutionContext("tenant", workspace, "analyst", permissions)


def profile(
    workspace: str = "workspace",
    *,
    metadata: dict[str, object] | None = None,
) -> DecisionEvolutionProfile:
    return DecisionEvolutionProfile(
        "profile",
        "Decision Quality",
        "Read-only historical decision analysis.",
        "tenant",
        workspace,
        "analyst",
        DECISION_SOURCES,
        NOW - timedelta(days=30),
        NOW,
        metadata=metadata or {},
    )


def decision(workspace: str = "workspace") -> DecisionRecord:
    return DecisionRecord(
        "decision",
        "profile",
        "tenant",
        workspace,
        "decision://center/1",
        "strategy",
        "context://1",
        "recommendation://1",
        "approval://1",
        ("evidence://1", "evidence://2"),
        0.8,
        "medium",
        "approved",
        NOW - timedelta(days=1),
    )


def configured_service() -> TikTokDecisionEvolutionCenter:
    service = TikTokDecisionEvolutionCenter()
    service.create_profile(profile(), context())
    service.record_decision(decision(), context())
    return service


def test_sources_are_bounded_read_only_scoped_and_offline() -> None:
    service = TikTokDecisionEvolutionCenter(max_results=25)
    service.create_profile(profile(), context())
    snapshots = service.collect("profile", context())
    assert set(snapshots) == set(DECISION_SOURCES)
    assert all(
        row["read_only"] and row["reference_only"]
        for rows in snapshots.values()
        for row in rows
    )
    adapter = ReferenceOnlyDecisionSource("decision_center")
    assert not hasattr(adapter, "execute")
    assert not hasattr(adapter, "approve")
    assert not hasattr(adapter, "publish")
    assert not hasattr(adapter, "configure")


def test_profile_lifecycle_approval_is_reference_only() -> None:
    service = TikTokDecisionEvolutionCenter()
    service.create_profile(profile(), context())
    for status in (
        ProfileStatus.COLLECTING,
        ProfileStatus.ANALYZING,
        ProfileStatus.READY,
        ProfileStatus.REVIEW,
        ProfileStatus.APPROVED_REFERENCE,
    ):
        service.transition_profile("profile", status, context())
    assert service.profiles["profile"].status is ProfileStatus.APPROVED_REFERENCE
    assert service.audit[-1]["approval_authorizes_execution"] is False
    with pytest.raises(ValueError, match="Invalid lifecycle"):
        service.transition_profile("profile", ProfileStatus.READY, context())


def test_time_result_metadata_rbac_and_scope_bounds() -> None:
    service = TikTokDecisionEvolutionCenter(max_range_days=30, max_results=2)
    too_wide = profile()
    too_wide.time_range_start = NOW - timedelta(days=31)
    with pytest.raises(ValueError, match="Time range"):
        service.create_profile(too_wide, context())
    with pytest.raises(ValueError, match="Secrets"):
        service.create_profile(profile(metadata={"session": "forbidden"}), context())
    service.create_profile(profile(), context())
    with pytest.raises(ValueError, match="result size"):
        service.items(service.profiles, context(), limit=3)
    with pytest.raises(PermissionError, match="RBAC"):
        service.analytics(context(permissions=frozenset()))
    with pytest.raises(PermissionError, match="Cross-tenant"):
        service.collect("profile", context("other"))


def test_records_outcomes_baselines_and_comparisons() -> None:
    service = configured_service()
    outcome = DecisionOutcome(
        "outcome",
        "decision",
        "tenant",
        "workspace",
        "Improve qualified engagement.",
        "analytics://outcome/1",
        ("engagement >= baseline",),
        "success",
        0.05,
        120.0,
        "metrics://resource/1",
        "risk://impact/1",
        None,
        ("evidence://outcome/1",),
    )
    service.record_outcome(outcome, context())
    baseline = DecisionBaseline(
        "baseline",
        "profile",
        "tenant",
        "workspace",
        0.7,
        60.0,
        0.75,
        0.25,
        0.9,
        0.72,
        0.2,
        "previous_30_days",
        30,
    )
    service.record_baseline(baseline, context())
    comparison = DecisionComparison(
        "comparison",
        "decision",
        "tenant",
        "workspace",
        "expected_vs_observed",
        0.7,
        0.8,
        0.1,
        "Observed result exceeded the expected reference value.",
    )
    service.compare(comparison, context())
    assert service.analytics(context())["decision_success_rate"] == 1
    bad = DecisionComparison(
        "bad",
        "decision",
        "tenant",
        "workspace",
        "expected_vs_observed",
        0.7,
        0.8,
        0.5,
        "Incorrect delta.",
    )
    with pytest.raises(ValueError, match="inconsistent"):
        service.compare(bad, context())


def test_patterns_require_evidence_and_never_claim_causality() -> None:
    service = configured_service()
    pattern = DecisionPattern(
        "pattern",
        "profile",
        "tenant",
        "workspace",
        "evidence_gap",
        "Lower evidence completeness co-occurred with failed outcomes.",
        ("evidence://pattern/1",),
        4,
    )
    service.identify_pattern(pattern, context())
    with pytest.raises(ValueError, match="causal"):
        service.identify_pattern(
            DecisionPattern(
                "causal",
                "profile",
                "tenant",
                "workspace",
                "failed_decision",
                "Unsupported cause.",
                ("evidence://pattern/2",),
                2,
                causal_claim=True,
            ),
            context(),
        )


def test_explainable_evaluation_and_confidence_calibration() -> None:
    service = configured_service()
    names = (
        "evidence_completeness",
        "constraint_compliance",
        "risk_calibration",
        "confidence_calibration",
        "outcome_accuracy",
        "resource_estimate_accuracy",
        "schedule_accuracy",
        "recovery_appropriateness",
        "approval_efficiency",
    )
    components = {
        name: (0.9 if name == "evidence_completeness" else 0.8, 1.0, f"{name}.")
        for name in names
    }
    evaluation = service.evaluate(
        "evaluation", "decision", components, context()
    )
    confidence = service.analyze_confidence(
        "confidence",
        "decision",
        "analytics://accuracy/1",
        0.7,
        (0.6, 0.7, 0.8),
        context(),
    )
    assert evaluation.decision_quality_score == pytest.approx(7.3 / 9)
    assert len(evaluation.score_breakdown) == 9
    assert confidence.calibration_difference == pytest.approx(-0.1)
    assert confidence.confidence_trend == "overconfident"
    assert confidence.explanation


def test_lessons_recommendations_handoffs_reviews_and_versions_are_advisory() -> None:
    service = configured_service()
    lesson = DecisionLesson(
        "lesson",
        "decision",
        "tenant",
        "workspace",
        ("Evidence was current.",),
        ("Approval was delayed.",),
        ("evidence://1",),
        ("evidence://missing/1",),
        (),
        ("risk volatility",),
        (),
        ("publication window",),
        ("manual recovery was appropriate",),
        "Add volatility evidence before human review.",
    )
    service.record_lesson(lesson, context())
    recommendation = service.recommend(
        "recommendation",
        "decision",
        "evidence",
        "Require current volatility evidence.",
        "Historical records showed an evidence gap.",
        ("evidence://1",),
        context(),
        handoffs=(
            "knowledge_evolution",
            "learning_center",
            "governance_center",
        ),
    )
    assert recommendation.advisory_only
    assert not recommendation.automatic_approval
    assert not recommendation.direct_execution
    assert recommendation.knowledge_evolution_handoff_reference
    review = DecisionReview(
        "review",
        "decision",
        "tenant",
        "workspace",
        "governance",
        "human-reviewer",
        ("Analysis is supported.",),
        ("Retain as reference.",),
        "approved",
        "audit://review/1",
    )
    review_only = context(
        permissions=frozenset({"tiktok:decision-evolution:review"})
    )
    service.review(review, review_only)
    first = service.version(
        "v1", "evaluation", "evaluation", ("created",), context()
    )
    second = service.version(
        "v2", "evaluation", "evaluation", ("calibrated",), context()
    )
    assert (first.version, second.version) == (1, 2)
    assert service.versions["v1"].superseded_by == "v2"
    assert service.audit[-3]["approval_authorizes_execution"] is False


def test_dashboard_api_metrics_history_and_analytics_contract() -> None:
    class App:
        def __init__(self) -> None:
            self.routes: list[tuple[str, list[str]]] = []

        def add_api_route(
            self, path: str, endpoint: object, **kwargs: object
        ) -> None:
            self.routes.append((path, list(kwargs["methods"])))

    service = configured_service()
    dashboard = service.dashboard(context())
    assert dashboard["decision_evolution_overview"]["advisory_only"]
    assert not dashboard["decision_evolution_overview"]["direct_execution"]
    assert not dashboard["decision_evolution_overview"]["captcha_bypass"]
    assert set(
        (
            "profiles",
            "decisions",
            "outcomes",
            "baselines",
            "patterns",
            "comparisons",
            "evaluations",
            "confidence",
            "lessons",
            "recommendations",
            "reviews",
            "versions",
            "history",
            "analytics",
        )
    ).issubset(dashboard["sections"])
    assert service.get_history(context())
    assert service.analytics(context())["decisions_total"] == 1
    assert all(name in service.metrics.render_prometheus() for name in METRIC_NAMES)
    app = App()
    register_decision_evolution_routes(app, service)
    assert set(ROUTES).issubset(path for path, _ in app.routes)
    assert all(methods == ["GET"] for _, methods in app.routes)
