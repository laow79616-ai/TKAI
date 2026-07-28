"""Safe, bounded and reviewable TikTok account activity orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from .adapters import (
    AccountCenterPort,
    BrowserRuntimePort,
    NullAccountCenterPort,
    NullBrowserRuntimePort,
    NullProxyCenterPort,
    ProxyCenterPort,
)
from .metrics import FarmingMetrics
from .models import (
    HIGH_RISK_BEHAVIORS,
    Approval,
    ApprovalStatus,
    BehaviorProfile,
    Execution,
    ExecutionStatus,
    FarmingPlan,
    FarmingSchedule,
    FarmingScope,
    HealthSignal,
    PlanStatus,
    Recommendation,
    ResourceLimits,
    RiskLevel,
    RiskScore,
)


class TikTokAccountFarming:
    """A control plane only; behavior drivers must remain approved and bounded."""

    def __init__(
        self,
        *,
        accounts: AccountCenterPort | None = None,
        browsers: BrowserRuntimePort | None = None,
        proxies: ProxyCenterPort | None = None,
        limits: ResourceLimits | None = None,
        auto_pause_threshold: float = 80,
        manual_review_threshold: float = 50,
    ) -> None:
        self.limits = limits or ResourceLimits()
        self.limits.validate()
        if not 0 <= manual_review_threshold <= auto_pause_threshold <= 100:
            raise ValueError("Risk thresholds must be ordered within [0, 100].")
        self.auto_pause_threshold = auto_pause_threshold
        self.manual_review_threshold = manual_review_threshold
        self.accounts = accounts or NullAccountCenterPort()
        self.browsers = browsers or NullBrowserRuntimePort()
        self.proxies = proxies or NullProxyCenterPort()
        self.profiles: dict[str, BehaviorProfile] = {}
        self.plans: dict[str, FarmingPlan] = {}
        self.schedules: dict[str, FarmingSchedule] = {}
        self.approvals: dict[str, Approval] = {}
        self.executions: dict[str, Execution] = {}
        self.signals: list[HealthSignal] = []
        self.risks: dict[str, RiskScore] = {}
        self.recommendations: dict[str, Recommendation] = {}
        self.audit: list[dict[str, str]] = []
        self.kill_switch = False
        self.paused_workspaces: set[tuple[str, str]] = set()
        self.metrics = FarmingMetrics()

    @staticmethod
    def _require(scope: FarmingScope, action: str) -> None:
        permission = f"tiktok:farming:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:farming:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: FarmingScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-workspace account-farming access denied.")

    def _audit(self, action: str, resource: str, scope: FarmingScope) -> None:
        self.audit.append(
            {
                "action": action,
                "resource": resource,
                "actor": scope.actor,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
            }
        )

    def create_profile(
        self, profile: BehaviorProfile, scope: FarmingScope
    ) -> BehaviorProfile:
        self._require(scope, "write")
        self._scoped(profile, scope)
        profile.validate()
        if profile.id in self.profiles:
            raise ValueError("Profile ID must be unique.")
        self.profiles[profile.id] = profile
        self._audit("profile.create", profile.id, scope)
        return profile

    def create_plan(self, plan: FarmingPlan, scope: FarmingScope) -> FarmingPlan:
        self._require(scope, "write")
        self._scoped(plan, scope)
        plan.validate()
        profile = self.profiles[plan.profile_reference]
        self._scoped(profile, scope)
        if plan.id in self.plans:
            raise ValueError("Plan ID must be unique.")
        if any(
            not self.accounts.validate(reference, scope.tenant, scope.workspace)
            for reference in plan.account_references
        ):
            raise ValueError("Account Center rejected an account reference.")
        self.plans[plan.id] = plan
        self.metrics.increment("tiktok_farming_plans_total")
        self._audit("plan.create", plan.id, scope)
        return plan

    def list_plans(self, scope: FarmingScope) -> list[FarmingPlan]:
        self._require(scope, "read")
        return [
            plan
            for plan in self.plans.values()
            if plan.tenant == scope.tenant
            and plan.workspace == scope.workspace
            and plan.status is not PlanStatus.DELETED
        ]

    def transition(
        self, plan_reference: str, status: PlanStatus, scope: FarmingScope
    ) -> FarmingPlan:
        self._require(scope, "write")
        plan = self.plans[plan_reference]
        self._scoped(plan, scope)
        transitions = {
            PlanStatus.DRAFT: {
                PlanStatus.PENDING_APPROVAL,
                PlanStatus.CANCELLED,
                PlanStatus.DELETED,
            },
            PlanStatus.PENDING_APPROVAL: {
                PlanStatus.READY,
                PlanStatus.DRAFT,
                PlanStatus.CANCELLED,
            },
            PlanStatus.READY: {
                PlanStatus.SCHEDULED,
                PlanStatus.RUNNING,
                PlanStatus.CANCELLED,
            },
            PlanStatus.SCHEDULED: {
                PlanStatus.RUNNING,
                PlanStatus.PAUSED,
                PlanStatus.CANCELLED,
            },
            PlanStatus.RUNNING: {
                PlanStatus.PAUSED,
                PlanStatus.COMPLETED,
                PlanStatus.FAILED,
                PlanStatus.CANCELLED,
            },
            PlanStatus.PAUSED: {
                PlanStatus.READY,
                PlanStatus.SCHEDULED,
                PlanStatus.CANCELLED,
                PlanStatus.FAILED,
            },
            PlanStatus.COMPLETED: {PlanStatus.ARCHIVED},
            PlanStatus.FAILED: {PlanStatus.READY, PlanStatus.ARCHIVED},
            PlanStatus.CANCELLED: {PlanStatus.ARCHIVED, PlanStatus.DELETED},
            PlanStatus.ARCHIVED: {PlanStatus.DELETED},
            PlanStatus.DELETED: set(),
        }
        if status not in transitions[plan.status]:
            raise ValueError(
                f"Invalid plan transition: {plan.status.value} -> {status.value}"
            )
        plan.status = status
        plan.updated_at = datetime.now(timezone.utc)
        self._audit(f"plan.{status.value}", plan.id, scope)
        return plan

    def create_schedule(
        self, schedule: FarmingSchedule, scope: FarmingScope
    ) -> FarmingSchedule:
        self._require(scope, "schedule")
        self._scoped(schedule, scope)
        schedule.validate()
        self._scoped(self.plans[schedule.plan_reference], scope)
        if schedule.id in self.schedules:
            raise ValueError("Schedule ID must be unique.")
        self.schedules[schedule.id] = schedule
        self._audit("schedule.create", schedule.id, scope)
        return schedule

    def request_approval(
        self,
        plan_reference: str,
        scope: FarmingScope,
        *,
        expiration: datetime | None = None,
    ) -> Approval:
        self._require(scope, "execute")
        plan = self.plans[plan_reference]
        self._scoped(plan, scope)
        profile = self.profiles[plan.profile_reference]
        approval = Approval(
            str(uuid4()),
            plan.id,
            scope.tenant,
            scope.workspace,
            scope.actor,
            set(profile.behaviors),
            approval_required=bool(profile.behaviors & HIGH_RISK_BEHAVIORS),
            expiration=expiration,
        )
        self.approvals[approval.id] = approval
        if plan.status is PlanStatus.DRAFT:
            self.transition(plan.id, PlanStatus.PENDING_APPROVAL, scope)
        self._audit("approval.request", approval.id, scope)
        return approval

    def decide_approval(
        self,
        approval_reference: str,
        scope: FarmingScope,
        *,
        approved: bool,
        notes: str = "",
        rejection_reason: str = "",
    ) -> Approval:
        self._require(scope, "approve")
        approval = self.approvals[approval_reference]
        self._scoped(approval, scope)
        if approval.status is not ApprovalStatus.PENDING:
            raise ValueError("Only pending approvals can be decided.")
        if approval.expiration and approval.expiration <= datetime.now(timezone.utc):
            approval.status = ApprovalStatus.EXPIRED
            raise ValueError("Approval has expired.")
        approval.reviewer = scope.actor
        approval.approval_notes = notes
        approval.rejection_reason = rejection_reason
        approval.status = (
            ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        )
        self.metrics.increment("tiktok_farming_approvals_total")
        plan = self.plans[approval.plan_reference]
        if approved:
            self.transition(plan.id, PlanStatus.READY, scope)
        else:
            self.transition(plan.id, PlanStatus.DRAFT, scope)
        self._audit(f"approval.{approval.status.value}", approval.id, scope)
        return approval

    def record_signal(self, signal: HealthSignal, scope: FarmingScope) -> RiskScore:
        self._require(scope, "signal")
        self._scoped(signal, scope)
        signal.validate()
        self.signals.append(signal)
        related = [
            item
            for item in self.signals
            if item.account_reference == signal.account_reference
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
        ]
        score = sum(item.value * item.confidence for item in related) / max(
            1, sum(item.confidence for item in related)
        )
        level = (
            RiskLevel.CRITICAL
            if score >= 90
            else RiskLevel.HIGH
            if score >= self.auto_pause_threshold
            else RiskLevel.MEDIUM
            if score >= self.manual_review_threshold
            else RiskLevel.LOW
        )
        risk = RiskScore(
            signal.account_reference,
            level,
            sorted({item.kind.value for item in related}),
            round(score, 2),
            signal.reason or f"Derived from {len(related)} bounded health signals.",
            "pause"
            if score >= self.auto_pause_threshold
            else "manual_review"
            if score >= self.manual_review_threshold
            else "continue",
            self.auto_pause_threshold,
            self.manual_review_threshold,
        )
        self.risks[signal.account_reference] = risk
        self.metrics.increment("tiktok_farming_risk_events_total")
        if score >= self.auto_pause_threshold:
            self.accounts.pause(
                signal.account_reference, scope.tenant, scope.workspace, risk.reason
            )
            for plan in self.list_plans(scope):
                if (
                    signal.account_reference in plan.account_references
                    and plan.status
                    in {PlanStatus.READY, PlanStatus.SCHEDULED, PlanStatus.RUNNING}
                ):
                    plan.status = PlanStatus.PAUSED
                    self.metrics.increment("tiktok_farming_pauses_total")
        self._audit("signal.record", signal.id, scope)
        return risk

    def recommend(self, plan_reference: str, scope: FarmingScope) -> Recommendation:
        self._require(scope, "read")
        plan = self.plans[plan_reference]
        self._scoped(plan, scope)
        profile = self.profiles[plan.profile_reference]
        scores = [
            self.risks[item].score
            for item in plan.account_references
            if item in self.risks
        ]
        risk = max(scores, default=0)
        recommendation = Recommendation(
            str(uuid4()),
            plan.id,
            "manual_review"
            if risk >= self.manual_review_threshold
            else "bounded_window",
            min(profile.session_duration_seconds.maximum, 900),
            max(profile.cooldown_seconds, 300),
            profile.action_count,
            risk >= self.auto_pause_threshold,
            [
                item.id
                for item in self.signals
                if item.account_reference in plan.account_references
            ],
            min(1.0, 0.5 + len(scores) * 0.1),
        )
        self.recommendations[recommendation.id] = recommendation
        return recommendation

    def execute(self, plan_reference: str, scope: FarmingScope) -> Execution:
        self._require(scope, "execute")
        if (
            self.kill_switch
            or (scope.tenant, scope.workspace) in self.paused_workspaces
        ):
            raise RuntimeError("Execution is disabled by a safety control.")
        if (
            sum(
                item.status is ExecutionStatus.RUNNING
                for item in self.executions.values()
            )
            >= self.limits.concurrency
        ):
            raise RuntimeError("Bounded execution concurrency reached.")
        plan = self.plans[plan_reference]
        self._scoped(plan, scope)
        if plan.status is not PlanStatus.READY:
            raise ValueError("Only ready plans can execute.")
        profile = self.profiles[plan.profile_reference]
        approvals = [
            item
            for item in self.approvals.values()
            if item.plan_reference == plan.id and item.status is ApprovalStatus.APPROVED
        ]
        if profile.behaviors & HIGH_RISK_BEHAVIORS and not approvals:
            raise PermissionError(
                "Explicit approval is required for high-risk actions."
            )
        execution = Execution(str(uuid4()), plan.id, scope.tenant, scope.workspace)
        self.executions[execution.id] = execution
        self.metrics.increment("tiktok_farming_executions_total")
        plan.status = PlanStatus.RUNNING
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = datetime.now(timezone.utc)
        resources: list[tuple[str, str]] = []
        try:
            for account in plan.account_references:
                if not self.accounts.validate(account, scope.tenant, scope.workspace):
                    raise RuntimeError("Account health validation failed.")
                browser = self.browsers.acquire(account, scope.tenant, scope.workspace)
                proxy = self.proxies.acquire(account, scope.tenant, scope.workspace)
                resources.extend((("browser", browser), ("proxy", proxy)))
                if not self.browsers.healthy(browser, scope.tenant, scope.workspace):
                    raise RuntimeError("Browser health validation failed.")
                if not self.proxies.healthy(proxy, scope.tenant, scope.workspace):
                    raise RuntimeError("Proxy health validation failed.")
                if not self.browsers.restore(browser, scope.tenant, scope.workspace):
                    raise RuntimeError("Session restore failed.")
                execution.checkpoint = f"validated:{account}"
            # This control plane intentionally does not contain a live action driver.
            execution.outcome = {
                "approved_plan": plan.id,
                "mode": plan.mode.value,
                "accounts_validated": len(plan.account_references),
                "actions_dispatched": 0,
                "bounded": True,
            }
            execution.status = ExecutionStatus.COMPLETED
            plan.status = PlanStatus.COMPLETED
            self.metrics.increment("tiktok_farming_success_total")
        except Exception:
            execution.status = ExecutionStatus.FAILED
            execution.attempts += 1
            plan.status = PlanStatus.FAILED
            self.metrics.increment("tiktok_farming_failures_total")
            raise
        finally:
            for kind, reference in reversed(resources):
                if kind == "browser":
                    self.browsers.release(reference, scope.tenant, scope.workspace)
                else:
                    self.proxies.release(reference, scope.tenant, scope.workspace)
            execution.finished_at = datetime.now(timezone.utc)
            if execution.started_at:
                self.metrics.set(
                    "tiktok_farming_latency_seconds",
                    (execution.finished_at - execution.started_at).total_seconds(),
                )
            self.metrics.set(
                "tiktok_farming_active_total",
                sum(
                    item.status is ExecutionStatus.RUNNING
                    for item in self.executions.values()
                ),
            )
            self._audit("execution.persist", execution.id, scope)
        return execution

    def retry(self, execution_reference: str, scope: FarmingScope) -> Execution:
        self._require(scope, "execute")
        previous = self.executions[execution_reference]
        self._scoped(previous, scope)
        if (
            previous.status is not ExecutionStatus.FAILED
            or previous.attempts >= previous.maximum_attempts
        ):
            raise ValueError("Execution is not eligible for bounded retry.")
        plan = self.plans[previous.plan_reference]
        plan.status = PlanStatus.READY
        return self.execute(plan.id, scope)

    def manual_stop(self, execution_reference: str, scope: FarmingScope) -> Execution:
        self._require(scope, "stop")
        execution = self.executions[execution_reference]
        self._scoped(execution, scope)
        execution.status = ExecutionStatus.CANCELLED
        self.plans[execution.plan_reference].status = PlanStatus.CANCELLED
        self._audit("execution.manual_stop", execution.id, scope)
        return execution

    def set_kill_switch(self, enabled: bool, scope: FarmingScope) -> None:
        self._require(scope, "admin")
        self.kill_switch = enabled
        if enabled:
            for execution in self.executions.values():
                if execution.status is ExecutionStatus.RUNNING:
                    execution.status = ExecutionStatus.PAUSED
        self._audit("safety.kill_switch", str(enabled).lower(), scope)

    def set_workspace_pause(self, enabled: bool, scope: FarmingScope) -> None:
        self._require(scope, "admin")
        key = (scope.tenant, scope.workspace)
        self.paused_workspaces.add(key) if enabled else self.paused_workspaces.discard(
            key
        )
        self._audit("safety.workspace_pause", str(enabled).lower(), scope)

    def dashboard(self, scope: FarmingScope) -> dict[str, Any]:
        self._require(scope, "read")
        plans = self.list_plans(scope)
        return {
            "sections": [
                "Plans",
                "Accounts",
                "Profiles",
                "Schedules",
                "Approvals",
                "Executions",
                "Signals",
                "Risk Scores",
                "Recommendations",
                "Failures",
                "Statistics",
            ],
            "plans": len(plans),
            "active": sum(
                plan.status in {PlanStatus.SCHEDULED, PlanStatus.RUNNING}
                for plan in plans
            ),
            "failures": sum(plan.status is PlanStatus.FAILED for plan in plans),
            "kill_switch": self.kill_switch,
            "metrics": self.metrics.snapshot(),
        }

    def analytics(self, scope: FarmingScope) -> dict[str, Any]:
        dashboard = self.dashboard(scope)
        return {
            "plans": dashboard["plans"],
            "active": dashboard["active"],
            "failures": dashboard["failures"],
            "risk_levels": {
                level.value: sum(score.level is level for score in self.risks.values())
                for level in RiskLevel
            },
            "metrics": self.metrics.snapshot(),
        }
