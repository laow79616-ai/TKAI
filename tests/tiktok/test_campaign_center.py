"""Offline coverage for the Enterprise TikTok Campaign Center."""

from __future__ import annotations

from datetime import timedelta

import pytest

from tiktok.campaign_center import (
    ApprovalStatus,
    Campaign,
    CampaignApproval,
    CampaignObjective,
    CampaignPlan,
    CampaignSchedule,
    CampaignScope,
    CampaignStatus,
    NullPlanningPort,
    ScheduleKind,
    TikTokCampaignCenter,
)
from tiktok.campaign_center.api import ROUTES, register_campaign_routes
from tiktok.campaign_center.metrics import METRIC_NAMES
from tiktok.campaign_center.models import utcnow


def scope(workspace: str = "workspace") -> CampaignScope:
    return CampaignScope(
        "tenant",
        workspace,
        "operator",
        frozenset({"tiktok:campaign:admin"}),
    )


def campaign(campaign_id: str = "campaign-1") -> Campaign:
    return Campaign(
        campaign_id,
        "Autumn launch",
        "Approval-gated local campaign",
        "workspace",
        "operator",
        CampaignObjective.PRODUCT_PROMOTION,
        "tenant",
    )


def plan(campaign_id: str = "campaign-1") -> CampaignPlan:
    return CampaignPlan(
        "plan-1",
        campaign_id,
        "tenant",
        "workspace",
        publishing_reference="ref://publishing/job-1",
        workflow_reference="ref://workflow/workflow-1",
        automation_reference="ref://automation/automation-1",
        execution_reference="ref://execution/plan-1",
        content_references=["kms://content/video-1"],
    )


def approved_center() -> tuple[TikTokCampaignCenter, NullPlanningPort]:
    planner = NullPlanningPort()
    center = TikTokCampaignCenter(operations_planner=planner)
    center.create(campaign(), scope())
    center.add_plan(plan(), scope())
    center.decide_approval(
        CampaignApproval(
            "approval-1",
            "campaign-1",
            "tenant",
            "workspace",
            "reviewer",
            ApprovalStatus.APPROVED,
            expires_at=utcnow() + timedelta(hours=1),
        ),
        scope(),
    )
    return center, planner


def test_campaign_crud_scope_version_and_secret_validation() -> None:
    center = TikTokCampaignCenter()
    created = center.create(campaign(), scope())
    assert created.version == 1
    updated = center.update(
        created.id, {"name": "Updated launch", "metadata": {"region": "CN"}}, scope()
    )
    assert updated.name == "Updated launch"
    assert updated.version == 2
    assert center.get(created.id, scope()).metadata == {"region": "CN"}
    assert len(center.list(scope())) == 1
    with pytest.raises(PermissionError, match="Cross-tenant"):
        center.get(created.id, scope("other"))
    unsafe = campaign("unsafe")
    unsafe.metadata = {"token": "must-not-be-logged"}
    with pytest.raises(ValueError, match="Secrets"):
        center.create(unsafe, scope())


def test_custom_objective_and_encrypted_reference_validation() -> None:
    custom = campaign()
    custom.objective = CampaignObjective.CUSTOM
    with pytest.raises(ValueError, match="objective reference"):
        custom.validate()
    custom.custom_objective_reference = "ref://objective/custom-1"
    custom.validate()
    invalid = plan()
    invalid.content_references = ["file://plaintext"]
    with pytest.raises(ValueError, match="encrypted or opaque"):
        invalid.validate()


def test_lifecycle_approval_enforcement_and_soft_delete() -> None:
    center = TikTokCampaignCenter()
    center.create(campaign(), scope())
    center.transition("campaign-1", CampaignStatus.PLANNING, scope())
    center.transition("campaign-1", CampaignStatus.REVIEW, scope())
    with pytest.raises(PermissionError, match="approval"):
        center.transition("campaign-1", CampaignStatus.APPROVED, scope())
    center.decide_approval(
        CampaignApproval(
            "approval-1",
            "campaign-1",
            "tenant",
            "workspace",
            "reviewer",
            ApprovalStatus.APPROVED,
        ),
        scope(),
    )
    approved = center.transition("campaign-1", CampaignStatus.APPROVED, scope())
    assert approved.status is CampaignStatus.APPROVED
    draft = center.create(campaign("draft-delete"), scope())
    deleted = center.delete(draft.id, scope())
    assert deleted.status is CampaignStatus.DELETED
    assert all(item.id != deleted.id for item in center.list(scope()))


def test_plans_dependencies_schedules_and_bounded_coordination() -> None:
    center, planner = approved_center()
    schedule = center.add_schedule(
        CampaignSchedule(
            "schedule-1",
            "campaign-1",
            "tenant",
            "workspace",
            ScheduleKind.ONE_TIME,
            "Asia/Shanghai",
            starts_at=utcnow() + timedelta(days=1),
            execution_window_seconds=1800,
        ),
        scope(),
    )
    center.plans["plan-1"].schedule_reference = schedule.id
    center.transition("campaign-1", CampaignStatus.PLANNING, scope())
    center.transition("campaign-1", CampaignStatus.REVIEW, scope())
    center.transition("campaign-1", CampaignStatus.APPROVED, scope())
    center.transition("campaign-1", CampaignStatus.SCHEDULED, scope())
    center.transition("campaign-1", CampaignStatus.RUNNING, scope())
    assert len(planner.registered) == 1
    assert planner.registered[0]["references"]["publishing"].startswith("ref://")

    invalid = CampaignSchedule(
        "invalid",
        "campaign-1",
        "tenant",
        "workspace",
        ScheduleKind.RECURRING,
        "UTC",
    )
    with pytest.raises(ValueError, match="recurrence"):
        center.add_schedule(invalid, scope())


class FakeStatus:
    def __init__(self, value: str) -> None:
        self.value = value

    def status(self, reference: str, tenant: str, workspace: str) -> str:
        assert tenant == "tenant"
        assert workspace == "workspace"
        return self.value if reference else "not_configured"


class FakeAnalytics:
    def campaign_kpis(
        self, campaign_id: str, tenant: str, workspace: str
    ) -> dict[str, float]:
        assert (campaign_id, tenant, workspace) == (
            "campaign-1",
            "tenant",
            "workspace",
        )
        return {
            "publishing_performance": 0.9,
            "execution_performance": 0.8,
            "resource_usage": 0.4,
            "completion_rate": 0.75,
            "trend": 0.1,
        }


def test_monitoring_analytics_history_dashboard_and_metrics() -> None:
    center = TikTokCampaignCenter(
        publishing_status=FakeStatus("ready"),
        workflow_status=FakeStatus("ready"),
        execution_status=FakeStatus("ready"),
        risk_status=FakeStatus("clear"),
        runtime_status=FakeStatus("healthy"),
        analytics_center=FakeAnalytics(),
    )
    center.create(campaign(), scope())
    center.add_plan(plan(), scope())
    health = center.monitoring("campaign-1", scope())
    assert health.campaign_health == "healthy"
    analytics = center.analytics("campaign-1", scope())
    assert analytics["completion_rate"] == 0.75
    assert center.history("campaign-1", scope())["audit_trail"]
    assert center.dashboard(scope())["sections"] == [
        "Campaign Overview",
        "Plans",
        "Schedules",
        "Monitoring",
        "Approvals",
        "Analytics",
        "History",
    ]
    rendered = center.metrics.render_prometheus()
    assert all(name in rendered for name in METRIC_NAMES)


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        assert callable(endpoint)
        assert tags == ["tiktok-campaign-center"]
        self.routes.append((path, tuple(methods)))


def test_api_dashboard_and_openapi_contracts() -> None:
    app = FakeApp()
    register_campaign_routes(app, TikTokCampaignCenter())
    paths = {path for path, _ in app.routes}
    assert set(ROUTES).issubset(paths)
    assert "/tiktok/campaigns/dashboard" in paths
    assert "/tiktok/campaigns/metrics" in paths
    assert "/tiktok/campaigns/approvals" in paths
    assert "/tiktok/campaigns/{campaign_id}/transition" in paths
    campaign_methods = {
        methods for path, methods in app.routes if path == "/tiktok/campaigns"
    }
    assert {("GET",), ("POST",)}.issubset(campaign_methods)


def test_rbac_and_expired_approvals() -> None:
    center = TikTokCampaignCenter()
    reader = CampaignScope("tenant", "workspace", "reader")
    with pytest.raises(PermissionError, match="write"):
        center.create(campaign(), reader)
    center.create(campaign(), scope())
    with pytest.raises(ValueError, match="past expiration"):
        center.decide_approval(
            CampaignApproval(
                "expired",
                "campaign-1",
                "tenant",
                "workspace",
                "reviewer",
                ApprovalStatus.APPROVED,
                expires_at=utcnow() - timedelta(seconds=1),
            ),
            scope(),
        )
