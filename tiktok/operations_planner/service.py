"""Explainable, approval-gated planning over existing TikTok control modules."""

from __future__ import annotations

from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import (
    HANDOFF_MODULES,
    INPUT_MODULES,
    ExecutionHandoffPort,
    NullExecutionHandoffPort,
    NullPlanningInputPort,
    PlanningInputPort,
)
from .metrics import PlannerMetrics
from .models import (
    Approval,
    ApprovalDecision,
    ApprovalKind,
    ExecutionHandoff,
    HistoryEntry,
    OperationsPlan,
    PlannerScope,
    PlanningSnapshot,
    PlanReview,
    PlanStatus,
    Recommendation,
    RiskLevel,
    Simulation,
    StrategyKind,
    utcnow,
    validate_safe_mapping,
)

TRANSITIONS: dict[PlanStatus, frozenset[PlanStatus]] = {
    PlanStatus.DRAFT: frozenset({PlanStatus.ANALYZING, PlanStatus.ARCHIVED}),
    PlanStatus.ANALYZING: frozenset({PlanStatus.PROPOSED, PlanStatus.FAILED}),
    PlanStatus.PROPOSED: frozenset({PlanStatus.PENDING_REVIEW, PlanStatus.DRAFT}),
    PlanStatus.PENDING_REVIEW: frozenset(
        {PlanStatus.APPROVED, PlanStatus.REJECTED, PlanStatus.DRAFT}
    ),
    PlanStatus.APPROVED: frozenset({PlanStatus.SCHEDULED, PlanStatus.PAUSED}),
    PlanStatus.SCHEDULED: frozenset({PlanStatus.EXECUTING, PlanStatus.PAUSED}),
    PlanStatus.EXECUTING: frozenset(
        {PlanStatus.COMPLETED, PlanStatus.PAUSED, PlanStatus.FAILED}
    ),
    PlanStatus.PAUSED: frozenset(
        {PlanStatus.SCHEDULED, PlanStatus.EXECUTING, PlanStatus.ARCHIVED}
    ),
    PlanStatus.COMPLETED: frozenset({PlanStatus.ARCHIVED}),
    PlanStatus.REJECTED: frozenset({PlanStatus.DRAFT, PlanStatus.ARCHIVED}),
    PlanStatus.FAILED: frozenset({PlanStatus.DRAFT, PlanStatus.ARCHIVED}),
    PlanStatus.ARCHIVED: frozenset({PlanStatus.DRAFT, PlanStatus.DELETED}),
    PlanStatus.DELETED: frozenset(),
}


class TikTokAIOperationsPlanner:
    """Creates bounded recommendations; existing engines retain execution ownership."""

    def __init__(
        self,
        inputs: dict[str, PlanningInputPort] | None = None,
        handoffs: dict[str, ExecutionHandoffPort] | None = None,
    ) -> None:
        null_input = NullPlanningInputPort()
        null_handoff = NullExecutionHandoffPort()
        self.inputs = {
            name: (inputs or {}).get(name, null_input) for name in INPUT_MODULES
        }
        self.handoffs = {
            name: (handoffs or {}).get(name, null_handoff) for name in HANDOFF_MODULES
        }
        self.plans: dict[str, OperationsPlan] = {}
        self.snapshots: dict[str, PlanningSnapshot] = {}
        self.recommendations: dict[str, Recommendation] = {}
        self.simulations: dict[str, Simulation] = {}
        self.approvals: dict[str, Approval] = {}
        self.executions: dict[str, ExecutionHandoff] = {}
        self.reviews: dict[str, PlanReview] = {}
        self.history: list[HistoryEntry] = []
        self.metrics = PlannerMetrics()
        self.kill_switches: set[tuple[str, str]] = set()
        self.workspace_pauses: set[tuple[str, str]] = set()
        self.account_pauses: set[tuple[str, str, str]] = set()

    @staticmethod
    def _require(scope: PlannerScope, permission: str) -> None:
        required = f"tiktok:planner:{permission}"
        if (
            required not in scope.permissions
            and "tiktok:planner:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: PlannerScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(self, plan: OperationsPlan, scope: PlannerScope, detail: str) -> None:
        forbidden = ("password=", "secret=", "token=", "cookie=", "session=")
        if any(marker in detail.casefold() for marker in forbidden):
            raise ValueError("Secrets are forbidden in planner audit records.")
        self.history.append(
            HistoryEntry(
                plan.id,
                plan.tenant,
                plan.workspace,
                plan.version,
                plan.status,
                scope.actor,
                detail,
            )
        )

    def scoped_values(self, values: Any, scope: PlannerScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def create_plan(self, plan: OperationsPlan, scope: PlannerScope) -> OperationsPlan:
        self._require(scope, "write")
        self._scoped(plan, scope)
        plan.validate()
        if plan.id in self.plans:
            raise ValueError("Plan ID must be unique.")
        self.plans[plan.id] = plan
        self.metrics.increment("tiktok_operations_plans_total")
        self._record(plan, scope, "plan.created")
        return plan

    def update_plan(
        self, reference: str, changes: dict[str, Any], scope: PlannerScope
    ) -> OperationsPlan:
        self._require(scope, "write")
        plan = self.plans[reference]
        self._scoped(plan, scope)
        if plan.status is not PlanStatus.DRAFT:
            raise ValueError("Only draft plans may be edited.")
        validate_safe_mapping(changes)
        allowed = {
            "name",
            "description",
            "priority",
            "strategy",
            "objectives",
            "constraints",
            "window_start",
            "window_end",
            "metadata",
        }
        if set(changes) - allowed:
            raise ValueError("Unsupported plan field.")
        for key, value in changes.items():
            setattr(plan, key, value)
        plan.version += 1
        plan.updated_at = utcnow()
        plan.validate()
        self._record(plan, scope, "plan.updated")
        return plan

    def transition(
        self, reference: str, status: PlanStatus, scope: PlannerScope
    ) -> OperationsPlan:
        self._require(scope, "write")
        plan = self.plans[reference]
        self._scoped(plan, scope)
        if status not in TRANSITIONS[plan.status]:
            raise ValueError(
                f"Invalid plan transition: {plan.status.value} -> {status.value}"
            )
        if status in {PlanStatus.APPROVED, PlanStatus.SCHEDULED, PlanStatus.EXECUTING}:
            self._valid_approval(reference, ApprovalKind.PLAN, scope)
        plan.status = status
        plan.version += 1
        plan.updated_at = utcnow()
        metric = {
            PlanStatus.PROPOSED: "tiktok_operations_plans_proposed_total",
            PlanStatus.APPROVED: "tiktok_operations_plans_approved_total",
            PlanStatus.REJECTED: "tiktok_operations_plans_rejected_total",
            PlanStatus.EXECUTING: "tiktok_operations_plans_executed_total",
            PlanStatus.FAILED: "tiktok_operations_plan_failures_total",
        }.get(status)
        if metric:
            self.metrics.increment(metric)
        self._record(plan, scope, f"plan.transition.{status.value}")
        return plan

    def collect_inputs(self, reference: str, scope: PlannerScope) -> PlanningSnapshot:
        self._require(scope, "analyze")
        plan = self.plans[reference]
        self._scoped(plan, scope)
        snapshot = PlanningSnapshot(
            plan.id,
            scope.tenant,
            scope.workspace,
            {name: port.snapshot(scope) for name, port in self.inputs.items()},
        )
        for name, value in snapshot.inputs.items():
            validate_safe_mapping(value)
            if value.get("restriction_active") or value.get("challenge_unresolved"):
                raise PermissionError(
                    f"Planning stopped by {name} restriction or challenge."
                )
        self.snapshots[reference] = snapshot
        return snapshot

    def analyze(self, reference: str, scope: PlannerScope) -> Recommendation:
        started = perf_counter()
        plan = self.plans[reference]
        self._scoped(plan, scope)
        if plan.status is PlanStatus.DRAFT:
            self.transition(reference, PlanStatus.ANALYZING, scope)
        if plan.status is not PlanStatus.ANALYZING:
            raise ValueError("Plan must be analyzing.")
        try:
            snapshot = self.collect_inputs(reference, scope)
            capacity = min(
                (float(value.get("capacity", 0)) for value in snapshot.inputs.values()),
                default=0,
            )
            requested = max((bound.requested for bound in plan.constraints), default=1)
            conflicts = [
                name
                for name, value in snapshot.inputs.items()
                if value.get("status") in {"paused", "unhealthy", "restricted"}
            ]
            conservative = plan.strategy in {
                StrategyKind.CONSERVATIVE,
                StrategyKind.RISK_REDUCTION,
                StrategyKind.MANUAL_ASSISTED,
            }
            concurrency = max(
                1, min(int(capacity), int(requested), 3 if conservative else 10)
            )
            risk = RiskLevel.HIGH if conflicts else RiskLevel.LOW
            confidence = max(0.05, min(0.99, 0.9 - len(conflicts) * 0.15))
            recommendation = Recommendation(
                f"recommendation-{plan.id}",
                plan.id,
                plan.tenant,
                plan.workspace,
                [
                    "review inputs",
                    "reserve bounded resources",
                    "schedule approved steps",
                ],
                [plan.planning_horizon.value],
                {"capacity": min(capacity, requested)},
                concurrency,
                60 if conservative else 30,
                conflicts,
                ["pause", "rollback to last checkpoint"],
                "Bounded objectives completed within validated capacity.",
                risk,
                confidence,
                [f"snapshot://{plan.id}/{name}" for name in snapshot.inputs],
            )
            self.recommendations[recommendation.id] = recommendation
            self.metrics.increment("tiktok_operations_plan_recommendations_total")
            self.metrics.set("tiktok_operations_plan_confidence", confidence)
            self.transition(reference, PlanStatus.PROPOSED, scope)
            return recommendation
        except Exception:
            if plan.status is PlanStatus.ANALYZING:
                self.transition(reference, PlanStatus.FAILED, scope)
            raise
        finally:
            self.metrics.set(
                "tiktok_operations_plan_latency_seconds", perf_counter() - started
            )

    def simulate(self, simulation: Simulation, scope: PlannerScope) -> Simulation:
        self._require(scope, "simulate")
        self._scoped(simulation, scope)
        plan = self.plans[simulation.plan_id]
        self._scoped(plan, scope)
        if simulation.live_access:
            raise ValueError("Simulations cannot use live TikTok access.")
        validate_safe_mapping(simulation.assumptions)
        simulation.result = {
            **simulation.result,
            "dry_run": True,
            "bounded": True,
            "strategy": plan.strategy.value,
        }
        self.simulations[simulation.id] = simulation
        self.metrics.increment("tiktok_operations_plan_simulations_total")
        self._record(plan, scope, f"simulation.{simulation.kind.value}")
        return simulation

    def decide(self, approval: Approval, scope: PlannerScope) -> Approval:
        self._require(scope, "approve")
        self._scoped(approval, scope)
        plan = self.plans[approval.plan_id]
        self._scoped(plan, scope)
        if approval.expires_at <= utcnow():
            raise ValueError("Approval expiration must be in the future.")
        if (
            approval.decision is ApprovalDecision.REJECTED
            and not approval.rejection_reason
        ):
            raise ValueError("Rejected approvals require a reason.")
        self.approvals[approval.id] = approval
        self._record(
            plan, scope, f"approval.{approval.kind.value}.{approval.decision.value}"
        )
        return approval

    def _valid_approval(
        self, plan_id: str, kind: ApprovalKind, scope: PlannerScope
    ) -> Approval:
        matches = [
            item
            for item in self.approvals.values()
            if item.plan_id == plan_id
            and item.kind is kind
            and item.decision is ApprovalDecision.APPROVED
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.expires_at > utcnow()
        ]
        if not matches:
            raise PermissionError(f"Valid {kind.value} approval required.")
        return matches[-1]

    def handoff(
        self, handoff: ExecutionHandoff, scope: PlannerScope
    ) -> ExecutionHandoff:
        self._require(scope, "execute")
        self._scoped(handoff, scope)
        plan = self.plans[handoff.plan_id]
        self._scoped(plan, scope)
        if plan.status is not PlanStatus.SCHEDULED:
            raise ValueError("Only approved and scheduled plans may be handed off.")
        self._valid_approval(plan.id, ApprovalKind.PLAN, scope)
        key = (scope.tenant, scope.workspace)
        if key in self.kill_switches or key in self.workspace_pauses:
            raise PermissionError("Kill switch or workspace pause is active.")
        handoff.accepted_references = {
            name: port.accept(handoff, scope) for name, port in self.handoffs.items()
        }
        self.executions[handoff.id] = handoff
        self.transition(plan.id, PlanStatus.EXECUTING, scope)
        self._record(plan, scope, "execution.reference_handoff")
        return handoff

    def add_review(self, review: PlanReview, scope: PlannerScope) -> PlanReview:
        self._require(scope, "review")
        self._scoped(review, scope)
        plan = self.plans[review.plan_id]
        self._scoped(plan, scope)
        self.reviews[review.id] = review
        self._record(plan, scope, "review.created")
        return review

    def analytics(self, scope: PlannerScope) -> dict[str, float]:
        self._require(scope, "read")
        plans = self.scoped_values(self.plans.values(), scope)
        completed = sum(plan.status is PlanStatus.COMPLETED for plan in plans)
        executed = sum(
            plan.status in {PlanStatus.EXECUTING, PlanStatus.COMPLETED}
            for plan in plans
        )
        return {
            "plans_created": float(len(plans)),
            "plans_approved": float(
                sum(plan.status is PlanStatus.APPROVED for plan in plans)
            ),
            "plans_rejected": float(
                sum(plan.status is PlanStatus.REJECTED for plan in plans)
            ),
            "plans_executed": float(executed),
            "plan_success_rate": completed / executed if executed else 0.0,
            "average_planning_time": self.metrics.values[
                "tiktok_operations_plan_latency_seconds"
            ],
            "prediction_accuracy_reference": 0.0,
            "resource_estimate_accuracy": 0.0,
            "schedule_accuracy": 0.0,
            "risk_reduction": 0.0,
        }

    def dashboard(self, scope: PlannerScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "title": "TikTok AI Operations Planner",
            "sections": (
                "Planner Overview",
                "Plans",
                "Objectives",
                "Strategies",
                "Constraints",
                "Resources",
                "Schedules",
                "Recommendations",
                "Simulations",
                "Approvals",
                "Executions",
                "Reviews",
                "History",
                "Analytics",
            ),
            "plans": [
                plan.to_dict()
                for plan in self.scoped_values(self.plans.values(), scope)
            ],
            "recommendations": [
                asdict(item)
                for item in self.scoped_values(self.recommendations.values(), scope)
            ],
            "analytics": self.analytics(scope),
        }
