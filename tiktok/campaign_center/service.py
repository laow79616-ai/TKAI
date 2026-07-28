"""Enterprise TikTok Campaign Center coordination service."""

from __future__ import annotations

from collections.abc import Iterable
from copy import deepcopy
from dataclasses import asdict
from time import monotonic
from typing import Any

from .adapters import (
    AnalyticsPort,
    NullAnalyticsPort,
    NullPlanningPort,
    NullReferencePort,
    NullStatusPort,
    PlanningPort,
    ReferencePort,
    StatusPort,
)
from .metrics import CampaignMetrics
from .models import (
    ApprovalStatus,
    Campaign,
    CampaignApproval,
    CampaignHealth,
    CampaignPlan,
    CampaignSchedule,
    CampaignScope,
    CampaignStatus,
    utcnow,
)

TRANSITIONS: dict[CampaignStatus, frozenset[CampaignStatus]] = {
    CampaignStatus.DRAFT: frozenset(
        {CampaignStatus.PLANNING, CampaignStatus.DELETED}
    ),
    CampaignStatus.PLANNING: frozenset(
        {CampaignStatus.REVIEW, CampaignStatus.DRAFT, CampaignStatus.DELETED}
    ),
    CampaignStatus.REVIEW: frozenset(
        {CampaignStatus.APPROVED, CampaignStatus.PLANNING}
    ),
    CampaignStatus.APPROVED: frozenset(
        {CampaignStatus.SCHEDULED, CampaignStatus.ARCHIVED}
    ),
    CampaignStatus.SCHEDULED: frozenset(
        {CampaignStatus.RUNNING, CampaignStatus.PAUSED}
    ),
    CampaignStatus.RUNNING: frozenset(
        {CampaignStatus.PAUSED, CampaignStatus.COMPLETED}
    ),
    CampaignStatus.PAUSED: frozenset(
        {CampaignStatus.RUNNING, CampaignStatus.ARCHIVED}
    ),
    CampaignStatus.COMPLETED: frozenset({CampaignStatus.ARCHIVED}),
    CampaignStatus.ARCHIVED: frozenset({CampaignStatus.DELETED}),
    CampaignStatus.DELETED: frozenset(),
}

ACTIVE_STATUSES = {
    CampaignStatus.PLANNING,
    CampaignStatus.REVIEW,
    CampaignStatus.APPROVED,
    CampaignStatus.SCHEDULED,
    CampaignStatus.RUNNING,
    CampaignStatus.PAUSED,
}


class TikTokCampaignCenter:
    """Coordinates existing modules without publishing or executing directly."""

    def __init__(
        self,
        *,
        creator: ReferencePort | None = None,
        content: ReferencePort | None = None,
        publishing: ReferencePort | None = None,
        workflow: ReferencePort | None = None,
        automation: ReferencePort | None = None,
        execution: ReferencePort | None = None,
        publishing_status: StatusPort | None = None,
        workflow_status: StatusPort | None = None,
        execution_status: StatusPort | None = None,
        risk_status: StatusPort | None = None,
        runtime_status: StatusPort | None = None,
        analytics_center: AnalyticsPort | None = None,
        operations_planner: PlanningPort | None = None,
    ) -> None:
        self.creator = creator or NullReferencePort()
        self.content = content or NullReferencePort()
        self.publishing = publishing or NullReferencePort()
        self.workflow = workflow or NullReferencePort()
        self.automation = automation or NullReferencePort()
        self.execution = execution or NullReferencePort()
        self.publishing_status = publishing_status or NullStatusPort()
        self.workflow_status = workflow_status or NullStatusPort()
        self.execution_status = execution_status or NullStatusPort()
        self.risk_status = risk_status or NullStatusPort()
        self.runtime_status = runtime_status or NullStatusPort()
        self.analytics_center = analytics_center or NullAnalyticsPort()
        self.operations_planner = operations_planner or NullPlanningPort()
        self.campaigns: dict[str, Campaign] = {}
        self.plans: dict[str, CampaignPlan] = {}
        self.schedules: dict[str, CampaignSchedule] = {}
        self.approvals: dict[str, CampaignApproval] = {}
        self.status_history: list[dict[str, str]] = []
        self.approval_history: list[dict[str, str]] = []
        self.execution_history: list[dict[str, str]] = []
        self.audit: list[dict[str, str]] = []
        self.metrics = CampaignMetrics()

    @staticmethod
    def _require(scope: CampaignScope, action: str) -> None:
        permission = f"tiktok:campaign:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:campaign:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: CampaignScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    @staticmethod
    def _visible(values: Iterable[Any], scope: CampaignScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _campaign(self, campaign_id: str, scope: CampaignScope) -> Campaign:
        campaign = self.campaigns[campaign_id]
        self._scoped(campaign, scope)
        return campaign

    def _audit(self, action: str, resource: str, scope: CampaignScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "occurred_at": utcnow().isoformat(),
            }
        )

    def _measure(self, started: float) -> None:
        self.metrics.set("tiktok_campaign_latency_seconds", monotonic() - started)

    def _refresh_metrics(self) -> None:
        values = list(self.campaigns.values())
        active = sum(item.status in ACTIVE_STATUSES for item in values)
        completed = sum(item.status is CampaignStatus.COMPLETED for item in values)
        terminal = sum(
            item.status in {CampaignStatus.COMPLETED, CampaignStatus.ARCHIVED}
            for item in values
        )
        self.metrics.set("tiktok_campaigns_total", float(len(values)))
        self.metrics.set("tiktok_campaign_active_total", float(active))
        self.metrics.set("tiktok_campaign_completed_total", float(completed))
        self.metrics.set(
            "tiktok_campaign_success_rate",
            completed / terminal if terminal else 0.0,
        )

    def create(self, campaign: Campaign, scope: CampaignScope) -> Campaign:
        started = monotonic()
        self._require(scope, "write")
        self._scoped(campaign, scope)
        campaign.validate()
        if campaign.id in self.campaigns:
            raise ValueError("Campaign ID must be unique.")
        self.campaigns[campaign.id] = deepcopy(campaign)
        self._audit("campaign.create", campaign.id, scope)
        self._refresh_metrics()
        self._measure(started)
        return deepcopy(campaign)

    def get(self, campaign_id: str, scope: CampaignScope) -> Campaign:
        self._require(scope, "read")
        return deepcopy(self._campaign(campaign_id, scope))

    def list(self, scope: CampaignScope) -> list[Campaign]:
        self._require(scope, "read")
        return [
            deepcopy(item)
            for item in self._visible(self.campaigns.values(), scope)
            if item.status is not CampaignStatus.DELETED
        ]

    def update(
        self, campaign_id: str, changes: dict[str, Any], scope: CampaignScope
    ) -> Campaign:
        started = monotonic()
        self._require(scope, "write")
        campaign = self._campaign(campaign_id, scope)
        immutable = {"id", "tenant", "workspace", "status", "version", "created_at"}
        if immutable & changes.keys():
            raise ValueError("Identity, scope, status, and version are immutable.")
        for key, value in changes.items():
            if not hasattr(campaign, key):
                raise ValueError(f"Unknown campaign field: {key}")
            setattr(campaign, key, value)
        campaign.version += 1
        campaign.updated_at = utcnow()
        campaign.validate()
        self._audit("campaign.update", campaign_id, scope)
        self._measure(started)
        return deepcopy(campaign)

    def transition(
        self, campaign_id: str, target: CampaignStatus, scope: CampaignScope
    ) -> Campaign:
        started = monotonic()
        self._require(scope, "transition")
        campaign = self._campaign(campaign_id, scope)
        source = campaign.status
        if target not in TRANSITIONS[source]:
            raise ValueError(
                f"Invalid campaign transition: {source.value} -> {target.value}"
            )
        if target is CampaignStatus.APPROVED and not self._active_approval(
            campaign_id, scope
        ):
            raise PermissionError("Active campaign approval required.")
        if target is CampaignStatus.SCHEDULED and not self._plans_for(
            campaign_id, scope
        ):
            raise ValueError("A campaign plan is required before scheduling.")
        if target is CampaignStatus.RUNNING:
            if not self._active_approval(campaign_id, scope):
                raise PermissionError("Approval enforcement denied campaign start.")
            self._coordinate(campaign_id, scope)
        campaign.status = target
        campaign.version += 1
        campaign.updated_at = utcnow()
        event = {
            "campaign_id": campaign_id,
            "from": source.value,
            "to": target.value,
            "actor": scope.actor,
            "occurred_at": campaign.updated_at.isoformat(),
            "tenant": scope.tenant,
            "workspace": scope.workspace,
        }
        self.status_history.append(event)
        if target in {
            CampaignStatus.RUNNING,
            CampaignStatus.PAUSED,
            CampaignStatus.COMPLETED,
        }:
            self.execution_history.append(dict(event))
        self._audit(f"campaign.{target.value}", campaign_id, scope)
        self._refresh_metrics()
        self._measure(started)
        return deepcopy(campaign)

    def delete(self, campaign_id: str, scope: CampaignScope) -> Campaign:
        campaign = self._campaign(campaign_id, scope)
        if campaign.status not in {
            CampaignStatus.DRAFT,
            CampaignStatus.PLANNING,
            CampaignStatus.ARCHIVED,
        }:
            raise ValueError(
                "Only draft, planning, or archived campaigns may be deleted."
            )
        return self.transition(campaign_id, CampaignStatus.DELETED, scope)

    def add_plan(self, plan: CampaignPlan, scope: CampaignScope) -> CampaignPlan:
        started = monotonic()
        self._require(scope, "write")
        self._scoped(plan, scope)
        self._campaign(plan.campaign_id, scope)
        plan.validate()
        if plan.id in self.plans:
            raise ValueError("Plan ID must be unique.")
        checks = (
            ("content", plan.content_references, self.content),
            ("publishing", [plan.publishing_reference], self.publishing),
            ("workflow", [plan.workflow_reference], self.workflow),
            ("automation", [plan.automation_reference], self.automation),
            ("execution", [plan.execution_reference], self.execution),
        )
        for label, references, port in checks:
            for reference in filter(None, references):
                if not port.exists(reference, scope.tenant, scope.workspace):
                    raise ValueError(f"{label.title()} reference was not found.")
        if plan.schedule_reference not in {"", *self.schedules.keys()}:
            raise ValueError("Schedule reference was not found.")
        campaign_plan_ids = {
            item.id for item in self._plans_for(plan.campaign_id, scope)
        }
        if not set(plan.dependencies).issubset(campaign_plan_ids):
            raise ValueError(
                "Plan dependencies must reference existing campaign plans."
            )
        self.plans[plan.id] = deepcopy(plan)
        self._audit("campaign.plan.create", plan.id, scope)
        self._measure(started)
        return deepcopy(plan)

    def add_schedule(
        self, schedule: CampaignSchedule, scope: CampaignScope
    ) -> CampaignSchedule:
        started = monotonic()
        self._require(scope, "write")
        self._scoped(schedule, scope)
        self._campaign(schedule.campaign_id, scope)
        schedule.validate()
        if schedule.id in self.schedules:
            raise ValueError("Schedule ID must be unique.")
        self.schedules[schedule.id] = deepcopy(schedule)
        self._audit("campaign.schedule.create", schedule.id, scope)
        self._measure(started)
        return deepcopy(schedule)

    def decide_approval(
        self, approval: CampaignApproval, scope: CampaignScope
    ) -> CampaignApproval:
        started = monotonic()
        self._require(scope, "approve")
        self._scoped(approval, scope)
        self._campaign(approval.campaign_id, scope)
        if not all((approval.id, approval.reviewer)):
            raise ValueError("Approval identity and reviewer are required.")
        if approval.status is ApprovalStatus.APPROVED:
            if approval.expires_at is not None and approval.expires_at <= utcnow():
                raise ValueError("Approved campaign cannot have a past expiration.")
            approval.decided_at = utcnow()
        self.approvals[approval.id] = deepcopy(approval)
        self.approval_history.append(
            {
                "campaign_id": approval.campaign_id,
                "approval_id": approval.id,
                "status": approval.status.value,
                "reviewer": approval.reviewer,
                "occurred_at": utcnow().isoformat(),
                "tenant": scope.tenant,
                "workspace": scope.workspace,
            }
        )
        self.metrics.increment("tiktok_campaign_approvals_total")
        self._audit("campaign.approval.decide", approval.id, scope)
        self._measure(started)
        return deepcopy(approval)

    def _active_approval(self, campaign_id: str, scope: CampaignScope) -> bool:
        return any(
            approval.campaign_id == campaign_id
            and approval.tenant == scope.tenant
            and approval.workspace == scope.workspace
            and approval.active
            for approval in self.approvals.values()
        )

    def _plans_for(
        self, campaign_id: str, scope: CampaignScope
    ) -> list[CampaignPlan]:
        return [
            item
            for item in self._visible(self.plans.values(), scope)
            if item.campaign_id == campaign_id
        ]

    def _coordinate(self, campaign_id: str, scope: CampaignScope) -> list[str]:
        """Register approved plans with Operations Planner; never execute them."""
        results = []
        for plan in self._plans_for(campaign_id, scope):
            results.append(
                self.operations_planner.register_campaign_plan(
                    campaign_id,
                    {
                        "publishing": plan.publishing_reference,
                        "workflow": plan.workflow_reference,
                        "automation": plan.automation_reference,
                        "execution": plan.execution_reference,
                        "schedule": plan.schedule_reference,
                    },
                    scope.tenant,
                    scope.workspace,
                )
            )
        return results

    def monitoring(
        self, campaign_id: str, scope: CampaignScope
    ) -> CampaignHealth:
        self._require(scope, "read")
        campaign = self._campaign(campaign_id, scope)
        plans = self._plans_for(campaign_id, scope)

        def first(name: str) -> str:
            return str(getattr(plans[0], name)) if plans else ""

        risk_reference = f"ref://campaign/{campaign_id}"
        statuses = {
            "publishing_status": self.publishing_status.status(
                first("publishing_reference"), scope.tenant, scope.workspace
            ),
            "workflow_status": self.workflow_status.status(
                first("workflow_reference"), scope.tenant, scope.workspace
            ),
            "execution_status": self.execution_status.status(
                first("execution_reference"), scope.tenant, scope.workspace
            ),
            "risk_status": self.risk_status.status(
                risk_reference, scope.tenant, scope.workspace
            ),
            "runtime_status": self.runtime_status.status(
                risk_reference, scope.tenant, scope.workspace
            ),
        }
        unhealthy = {"failed", "blocked", "restricted", "unavailable", "unhealthy"}
        health = "attention" if unhealthy & set(statuses.values()) else "healthy"
        if campaign.status in {CampaignStatus.PAUSED, CampaignStatus.DELETED}:
            health = campaign.status.value
        return CampaignHealth(
            campaign_id=campaign_id,
            campaign_health=health,
            checked_at=utcnow(),
            **statuses,
        )

    def analytics(self, campaign_id: str, scope: CampaignScope) -> dict[str, Any]:
        self._require(scope, "read")
        campaign = self._campaign(campaign_id, scope)
        kpis = self.analytics_center.campaign_kpis(
            campaign_id, scope.tenant, scope.workspace
        )
        return {
            "campaign_id": campaign_id,
            "status": campaign.status.value,
            "campaign_kpis": kpis,
            "publishing_performance": kpis.get("publishing_performance", 0.0),
            "execution_performance": kpis.get("execution_performance", 0.0),
            "resource_usage": kpis.get("resource_usage", 0.0),
            "completion_rate": kpis.get("completion_rate", 0.0),
            "trend": kpis.get("trend", 0.0),
        }

    def history(self, campaign_id: str, scope: CampaignScope) -> dict[str, Any]:
        self._require(scope, "read")
        self._campaign(campaign_id, scope)

        def matching(values: list[dict[str, str]]) -> list[dict[str, str]]:
            return [
                dict(item)
                for item in values
                if item.get("campaign_id") == campaign_id
                and item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
            ]

        return {
            "status_history": matching(self.status_history),
            "approval_history": matching(self.approval_history),
            "execution_history": matching(self.execution_history),
            "audit_trail": [
                dict(item)
                for item in self.audit
                if item["tenant"] == scope.tenant
                and item["workspace"] == scope.workspace
                and (
                    item["resource"] == campaign_id
                    or item["resource"] in self.plans
                    or item["resource"] in self.schedules
                    or item["resource"] in self.approvals
                )
            ],
        }

    def dashboard(self, scope: CampaignScope) -> dict[str, Any]:
        self._require(scope, "read")
        campaigns = self.list(scope)
        return {
            "sections": [
                "Campaign Overview",
                "Plans",
                "Schedules",
                "Monitoring",
                "Approvals",
                "Analytics",
                "History",
            ],
            "overview": {
                "total": len(campaigns),
                "active": sum(item.status in ACTIVE_STATUSES for item in campaigns),
                "completed": sum(
                    item.status is CampaignStatus.COMPLETED for item in campaigns
                ),
                "by_status": {
                    status.value: sum(item.status is status for item in campaigns)
                    for status in CampaignStatus
                },
            },
            "plans": len(self._visible(self.plans.values(), scope)),
            "schedules": len(self._visible(self.schedules.values(), scope)),
            "approvals": len(self._visible(self.approvals.values(), scope)),
            "metrics": self.metrics.snapshot(),
        }

    def export_campaign(self, campaign_id: str, scope: CampaignScope) -> dict[str, Any]:
        """Serializable API view with no plaintext secrets."""
        campaign = self.get(campaign_id, scope)
        return {
            "campaign": campaign.to_dict(),
            "plans": [asdict(plan) for plan in self._plans_for(campaign_id, scope)],
            "analytics": self.analytics(campaign_id, scope),
        }
