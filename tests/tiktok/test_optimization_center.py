"""Offline coverage for the Enterprise TikTok AI Continuous Optimization Center."""

from __future__ import annotations

from datetime import timedelta

import pytest

from tiktok.optimization_center import (
    Approval,
    Baseline,
    CandidateChange,
    CandidateKind,
    ChangeRecord,
    Evaluation,
    Experiment,
    ExperimentKind,
    OptimizationProfile,
    OptimizationScope,
    OptimizationStatus,
    Recommendation,
    RequestScope,
    RiskLevel,
    Signal,
    ValidationResult,
)
from tiktok.optimization_center.adapters import BoundedTestDouble
from tiktok.optimization_center.api import ROUTES
from tiktok.optimization_center.metrics import METRIC_NAMES
from tiktok.optimization_center.models import utcnow
from tiktok.optimization_center.service import (
    TikTokAIContinuousOptimizationCenter,
)


def scope(workspace: str = "workspace") -> RequestScope:
    return RequestScope(
        "tenant",
        workspace,
        "operator",
        frozenset({"tiktok:optimization:admin"}),
    )


def profile() -> OptimizationProfile:
    return OptimizationProfile(
        "profile-1",
        "Runtime reliability",
        "Bounded local optimization",
        "tenant",
        "workspace",
        "operator",
        OptimizationScope.RUNTIME,
    )


def candidate(proposed: float = 11) -> CandidateChange:
    return CandidateChange(
        "candidate-1",
        "profile-1",
        "tenant",
        "workspace",
        CandidateKind.CONCURRENCY,
        OptimizationScope.RUNTIME,
        "worker_concurrency",
        10,
        proposed,
        1,
        ["decision://evidence/1"],
    )


def recommendation() -> Recommendation:
    return Recommendation(
        "recommendation-1",
        "candidate-1",
        "tenant",
        "workspace",
        OptimizationScope.RUNTIME,
        10,
        11,
        "Improve queue latency",
        RiskLevel.LOW,
        0.85,
        ["decision://evidence/1"],
        "Observe health for five minutes",
        "Restore checkpoint on regression",
    )


def ready_center() -> tuple[TikTokAIContinuousOptimizationCenter, BoundedTestDouble]:
    adapter = BoundedTestDouble()
    center = TikTokAIContinuousOptimizationCenter(adapter, adapter, adapter)
    center.create_profile(profile(), scope())
    center.add_candidate(candidate(), scope())
    center.recommend(recommendation(), scope())
    return center, adapter


def approve(center: TikTokAIContinuousOptimizationCenter) -> None:
    center.transition("profile-1", OptimizationStatus.COLLECTING, scope())
    center.transition("profile-1", OptimizationStatus.ANALYZING, scope())
    center.transition("profile-1", OptimizationStatus.PROPOSED, scope())
    center.transition("profile-1", OptimizationStatus.PENDING_REVIEW, scope())
    center.decide(
        Approval(
            "approval-1",
            "recommendation-1",
            "tenant",
            "workspace",
            "reviewer",
            "bounded and reversible",
            True,
            utcnow() + timedelta(hours=1),
        ),
        "profile-1",
        scope(),
    )
    center.transition("profile-1", OptimizationStatus.APPROVED, scope())


def change() -> ChangeRecord:
    return ChangeRecord(
        "change-1",
        "recommendation-1",
        "tenant",
        "workspace",
        "configuration://runtime",
        1,
        "backup://runtime/1",
        "checkpoint://runtime/1",
    )


def test_lifecycle_baseline_signals_candidates_experiments_and_evaluation() -> None:
    center = TikTokAIContinuousOptimizationCenter()
    center.create_profile(profile(), scope())
    center.transition("profile-1", OptimizationStatus.COLLECTING, scope())
    baseline = center.capture_baseline(
        Baseline(
            "baseline-1",
            "profile-1",
            "tenant",
            "workspace",
            1,
            "configuration://runtime",
            {"workers": 10},
            {},
            "healthy",
        ),
        scope(),
    )
    assert baseline.metrics["utilization"] == 0.75
    center.add_signal(
        Signal(
            "signal-1",
            "profile-1",
            "tenant",
            "workspace",
            "queue_trend",
            0.8,
            ["decision://evidence/1"],
        ),
        scope(),
    )
    center.add_candidate(candidate(), scope())
    center.record_experiment(
        Experiment(
            "experiment-1",
            "candidate-1",
            "tenant",
            "workspace",
            ExperimentKind.DRY_RUN,
            "simulation://1",
            0.1,
            0.09,
            False,
        ),
        scope(),
    )
    center.evaluate(
        Evaluation(
            "evaluation-1",
            "candidate-1",
            "tenant",
            "workspace",
            0.1,
            0.09,
            RiskLevel.LOW,
            0.85,
            ["simulation://1"],
            "failure rate increases",
        ),
        scope(),
    )
    assert center.metrics.values["tiktok_optimization_experiments_total"] == 1


def test_recommendations_are_advisory_and_human_approval_is_enforced() -> None:
    center, adapter = ready_center()
    with pytest.raises(PermissionError, match="human approval"):
        center.apply_change(change(), "profile-1", scope())
    assert adapter.applied == []
    approve(center)
    applied = center.apply_change(change(), "profile-1", scope())
    assert applied.result_reference == "bounded-change://candidate-1"
    assert adapter.applied == ["candidate-1"]


def test_version_backup_checkpoint_and_change_bounds_are_enforced() -> None:
    center, _ = ready_center()
    approve(center)
    invalid = change()
    invalid.backup_reference = "plaintext"
    with pytest.raises(ValueError, match="backup"):
        center.apply_change(invalid, "profile-1", scope())
    with pytest.raises(ValueError, match="maximum"):
        candidate(20).validate()
    unsafe = candidate()
    unsafe.parameter = "captcha_bypass"
    with pytest.raises(ValueError, match="Unsafe"):
        unsafe.validate()


def test_post_change_regression_triggers_automatic_rollback() -> None:
    center, adapter = ready_center()
    approve(center)
    center.apply_change(change(), "profile-1", scope())
    center.validate_change(
        ValidationResult(
            "validation-1",
            "change-1",
            "tenant",
            "workspace",
            "degraded",
            -0.2,
            0.1,
            0.2,
            -0.1,
            "elevated",
            True,
            False,
        ),
        "profile-1",
        scope(),
    )
    assert adapter.rolled_back == ["candidate-1"]
    assert center.profiles["profile-1"].status is OptimizationStatus.ROLLED_BACK


def test_isolation_rbac_safe_metadata_and_evidence_requirements() -> None:
    center = TikTokAIContinuousOptimizationCenter()
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.create_profile(profile(), scope("other"))
    unsafe = profile()
    unsafe.metadata = {"cookie": "forbidden"}
    with pytest.raises(ValueError, match="Secrets"):
        center.create_profile(unsafe, scope())
    with pytest.raises(PermissionError, match="write"):
        center.create_profile(profile(), RequestScope("tenant", "workspace", "reader"))


def test_api_dashboard_history_analytics_and_metrics_contracts() -> None:
    center, _ = ready_center()
    assert len(ROUTES) == 14
    assert len(center.dashboard(scope())["sections"]) == 16
    assert center.history(scope())["profile_versions"]
    assert center.analytics(scope())["recommendations_generated"] == 1
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)
