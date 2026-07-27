from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from tiktok.account_farming import (
    METRICS,
    ApprovalStatus,
    BehaviorCategory,
    BehaviorProfile,
    Bounds,
    FarmingMode,
    FarmingPlan,
    FarmingSchedule,
    FarmingScope,
    HealthSignal,
    PlanStatus,
    ResourceLimits,
    RiskLevel,
    ScheduleKind,
    SignalKind,
    TikTokAccountFarming,
)


class Accounts:
    def __init__(self) -> None:
        self.paused: list[str] = []

    def validate(self, reference, tenant, workspace):
        return reference.startswith("account-") and tenant == "tenant-a"

    def pause(self, reference, tenant, workspace, reason):
        self.paused.append(reference)


@pytest.fixture
def scope():
    return FarmingScope(
        "tenant-a",
        "workspace-a",
        "operator",
        frozenset({"tiktok:farming:admin"}),
    )


@pytest.fixture
def service(scope):
    result = TikTokAccountFarming(
        accounts=Accounts(), limits=ResourceLimits(concurrency=2)
    )
    result.create_profile(
        BehaviorProfile(
            "profile-1",
            scope.tenant,
            scope.workspace,
            "Reviewed profile",
            {
                BehaviorCategory.FEED_BROWSING,
                BehaviorCategory.LIKE_ACTION_INTERFACE,
            },
            action_count=Bounds(0, 3),
        ),
        scope,
    )
    result.create_plan(
        FarmingPlan(
            "plan-1",
            "Bounded plan",
            "Reviewable test plan",
            scope.tenant,
            scope.workspace,
            scope.actor,
            ["account-1"],
            "profile-1",
            mode=FarmingMode.DRY_RUN,
        ),
        scope,
    )
    return result


def test_plan_profile_lifecycle_and_isolation(service, scope):
    plan = service.plans["plan-1"]
    assert plan.status is PlanStatus.DRAFT
    approval = service.request_approval(plan.id, scope)
    assert plan.status is PlanStatus.PENDING_APPROVAL
    service.decide_approval(approval.id, scope, approved=True, notes="bounded")
    assert approval.status is ApprovalStatus.APPROVED
    assert plan.status is PlanStatus.READY
    assert service.list_plans(FarmingScope("tenant-a", "workspace-b", "intruder")) == []


def test_bounds_schedules_and_approval_expiry(service, scope):
    with pytest.raises(ValueError):
        ResourceLimits(concurrency=0).validate()
    schedule = FarmingSchedule(
        "schedule-1",
        "plan-1",
        scope.tenant,
        scope.workspace,
        ScheduleKind.INTERVAL,
        interval_seconds=300,
        maximum_runs=10,
    )
    assert service.create_schedule(schedule, scope) is schedule
    approval = service.request_approval(
        "plan-1", scope, expiration=datetime.now(timezone.utc) - timedelta(seconds=1)
    )
    with pytest.raises(ValueError, match="expired"):
        service.decide_approval(approval.id, scope, approved=True)


def test_approval_enforcement_execution_metrics_and_resources(service, scope):
    service.request_approval("plan-1", scope)
    service.plans["plan-1"].status = PlanStatus.READY
    with pytest.raises(PermissionError):
        service.execute("plan-1", scope)
    approval = next(iter(service.approvals.values()))
    approval.status = ApprovalStatus.APPROVED
    execution = service.execute("plan-1", scope)
    assert execution.outcome["actions_dispatched"] == 0
    assert execution.outcome["bounded"] is True
    assert service.plans["plan-1"].status is PlanStatus.COMPLETED
    assert set(service.metrics.snapshot()) == set(METRICS)


def test_signals_risk_recommendation_auto_pause_and_kill_switch(service, scope):
    service.plans["plan-1"].status = PlanStatus.READY
    risk = service.record_signal(
        HealthSignal(
            "signal-1",
            scope.tenant,
            scope.workspace,
            "account-1",
            SignalKind.RESTRICTION,
            95,
            1,
            "restriction reported",
        ),
        scope,
    )
    assert risk.level is RiskLevel.CRITICAL
    assert service.accounts.paused == ["account-1"]
    assert service.plans["plan-1"].status is PlanStatus.PAUSED
    recommendation = service.recommend("plan-1", scope)
    assert recommendation.advisory_only and recommendation.suggested_pause
    service.set_kill_switch(True, scope)
    service.plans["plan-1"].status = PlanStatus.READY
    with pytest.raises(RuntimeError, match="safety"):
        service.execute("plan-1", scope)


def test_dashboard_api_contract(service, scope):
    dashboard = service.dashboard(scope)
    assert {"Plans", "Approvals", "Risk Scores", "Statistics"} <= set(
        dashboard["sections"]
    )

    from tiktok.account_farming.api import ROUTES, register_account_farming_routes

    class App:
        def __init__(self):
            self.routes = []

        def add_api_route(self, path, endpoint, methods, tags):
            self.routes.append((path, methods, endpoint, tags))

    app = App()
    register_account_farming_routes(app, service)
    paths = {item[0] for item in app.routes}
    assert set(ROUTES) <= paths
    assert "/tiktok/account-farming/dashboard" in paths


def test_no_forbidden_behavior_or_sensitive_fields(service):
    serialized = str(service.plans["plan-1"].to_dict()).casefold()
    for forbidden in (
        "captcha bypass",
        "security bypass",
        "restriction circumvention",
        "bulk messaging",
        "mass following",
        "telegram",
        "whatsapp",
        "facebook",
        "instagram",
        "discord",
    ):
        assert forbidden not in serialized
