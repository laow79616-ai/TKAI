from __future__ import annotations

from datetime import timedelta

import pytest

from tiktok.risk_control import (
    HealthStatus,
    Lifecycle,
    PolicyKind,
    RecoveryRecord,
    ReviewDecision,
    RiskAction,
    RiskLevel,
    RiskLimit,
    RiskPolicy,
    RiskProfile,
    RiskReview,
    RiskRule,
    RiskScope,
    RiskSignal,
    RuleOperator,
    SignalKind,
    TikTokRiskControlCenter,
)
from tiktok.risk_control.api import ROUTES, register_risk_control_routes
from tiktok.risk_control.metrics import METRIC_NAMES
from tiktok.risk_control.models import utcnow


class Port:
    def __init__(self, recovery: bool = True) -> None:
        self.calls: list[tuple[str, str, str]] = []
        self.recovery = recovery

    def apply(self, action: str, reference: str, reason: str) -> None:
        self.calls.append((action, reference, reason))

    def recover(self, reference: str, checkpoint: str) -> bool:
        self.calls.append(("recover", reference, checkpoint))
        return self.recovery


def scope(
    workspace: str = "w1", permissions: frozenset[str] | None = None
) -> RiskScope:
    return RiskScope(
        "tenant-1",
        workspace,
        "operator",
        permissions or frozenset({"tiktok:risk:admin"}),
    )


def profile(workspace: str = "w1") -> RiskProfile:
    return RiskProfile(
        "p1", "Primary", "risk profile", "tenant-1", workspace, "owner", "account-1"
    )


def active_center() -> tuple[TikTokRiskControlCenter, RiskScope]:
    center, request_scope = TikTokRiskControlCenter(), scope()
    center.create_profile(profile(), request_scope)
    center.transition_profile("p1", Lifecycle.ACTIVE, request_scope)
    return center, request_scope


def test_profile_lifecycle_validation_and_isolation() -> None:
    center, request_scope = active_center()
    center.transition_profile("p1", Lifecycle.MONITORING, request_scope)
    with pytest.raises(ValueError):
        center.transition_profile("p1", Lifecycle.DRAFT, request_scope)
    with pytest.raises(PermissionError):
        center.transition_profile("p1", Lifecycle.PAUSED, scope("other"))
    with pytest.raises(ValueError):
        center.create_profile(
            RiskProfile(
                "bad",
                "Bad",
                "",
                "tenant-1",
                "w1",
                "owner",
                "",
                metadata={"cookie": "plaintext"},
            ),
            request_scope,
        )


def test_bounded_policy_rules_limits_and_scoring() -> None:
    center, request_scope = active_center()
    policy = center.create_policy(
        RiskPolicy("policy-1", "tenant-1", "w1", "Account Safety", PolicyKind.ACCOUNT),
        request_scope,
    )
    center.create_rule(
        RiskRule(
            "rule-1",
            "tenant-1",
            "w1",
            policy.id,
            RuleOperator.TREND_MATCH,
            RiskAction.REQUIRE_REVIEW,
            SignalKind.LOGIN_FAILURE,
            trend_count=2,
        ),
        request_scope,
    )
    center.set_limit(
        RiskLimit("limit-1", "tenant-1", "w1", "account", "account-1"), request_scope
    )
    for index in range(2):
        center.ingest_signal(
            RiskSignal(
                f"s-{index}",
                "tenant-1",
                "w1",
                SignalKind.LOGIN_FAILURE,
                "account-center",
                8,
                0.9,
                "account-1",
            ),
            request_scope,
        )
    score = center.evaluate("p1", request_scope)
    assert score.score > 60
    assert score.level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
    assert score.recommended_action is RiskAction.REQUIRE_REVIEW
    assert score.explanation
    with pytest.raises(ValueError):
        center.create_rule(
            RiskRule(
                "bad",
                "tenant-1",
                "w1",
                policy.id,
                RuleOperator.THRESHOLD_MATCH,
                RiskAction.NOTIFY,
                threshold=101,
            ),
            request_scope,
        )
    with pytest.raises(ValueError):
        center.set_limit(
            RiskLimit("bad", "tenant-1", "w1", "account", "a", concurrency=1001),
            request_scope,
        )


def test_approval_enforcement_pause_and_coordinated_port() -> None:
    account_port = Port()
    center = TikTokRiskControlCenter(accounts=account_port)
    request_scope = scope()
    item = center.create_profile(profile(), request_scope)
    center.transition_profile("p1", Lifecycle.ACTIVE, request_scope)
    item.risk_level = RiskLevel.HIGH
    with pytest.raises(PermissionError):
        center.execute_action(RiskAction.PAUSE_ACCOUNT, item, request_scope)
    review = center.create_review(
        RiskReview(
            "review-1", "tenant-1", "w1", "p1", "reviewer", ("evidence://event/1",)
        ),
        request_scope,
    )
    center.decide_review(review.id, ReviewDecision.APPROVED, "validated", request_scope)
    center.execute_action(
        RiskAction.PAUSE_ACCOUNT, item, request_scope, approval_reference=review.id
    )
    assert account_port.calls[0][0] == "pause"
    assert next(iter(center.pauses.values())).active
    assert center.audit


def test_recovery_stops_for_unresolved_platform_condition() -> None:
    center, request_scope = active_center()
    recovery = RecoveryRecord(
        "recovery-1",
        "tenant-1",
        "w1",
        "p1",
        unresolved_platform_condition=True,
    )
    result = center.recover(recovery, request_scope)
    assert result.outcome == "stopped_unresolved_platform_condition"
    assert result.attempts == 0


def test_approved_recovery_health_alert_analytics_and_metrics() -> None:
    port = Port()
    center = TikTokRiskControlCenter(accounts=port)
    request_scope = scope()
    item = center.create_profile(profile(), request_scope)
    center.transition_profile("p1", Lifecycle.ACTIVE, request_scope)
    item.risk_level = RiskLevel.CRITICAL
    center.execute_action(RiskAction.PAUSE_ACCOUNT, item, request_scope)
    center.create_review(
        RiskReview("review-1", "tenant-1", "w1", "p1", "reviewer"),
        request_scope,
    )
    center.decide_review("review-1", ReviewDecision.APPROVED, "safe", request_scope)
    result = center.recover(
        RecoveryRecord(
            "recovery-1", "tenant-1", "w1", "p1", checkpoint_reference="checkpoint-1"
        ),
        request_scope,
        "review-1",
    )
    assert result.outcome == "succeeded"
    health = center.update_health(
        HealthStatus("health-1", "tenant-1", "w1", "account-1", login=80),
        request_scope,
    )
    assert health.composite == 97.5
    alert = center.acknowledge_alert("alert-1", request_scope)
    assert alert.acknowledged_by == "operator"
    assert center.analytics(request_scope)["recovery_success_rate"] == 1
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)


def test_expired_review_and_rbac() -> None:
    center, request_scope = active_center()
    center.create_review(
        RiskReview(
            "expired",
            "tenant-1",
            "w1",
            "p1",
            "reviewer",
            expires_at=utcnow() - timedelta(seconds=1),
        ),
        request_scope,
    )
    with pytest.raises(ValueError):
        center.decide_review("expired", ReviewDecision.APPROVED, "", request_scope)
    with pytest.raises(PermissionError):
        center.list_profiles(scope(permissions=frozenset({"tiktok:risk:signal"})))


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[str] = []

    def add_api_route(self, path: str, endpoint: object, **kwargs: object) -> None:
        self.routes.append(path)


def test_api_dashboard_and_route_contract() -> None:
    app = FakeApp()
    register_risk_control_routes(app, TikTokRiskControlCenter())
    assert set(ROUTES).issubset(app.routes)
    assert "/tiktok/risk-control/dashboard" in app.routes
    assert "/tiktok/risk-control/metrics" in app.routes
