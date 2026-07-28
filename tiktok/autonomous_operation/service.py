"""Approval-gated orchestration over existing TikTok execution modules."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict
from time import perf_counter
from typing import Any

from .adapters import DELEGATION_MODULES, MissionDelegationPort, ReferenceOnlyPort
from .metrics import AutonomousMetrics
from .models import (
    AuditEntry,
    ExecutionState,
    Mission,
    MissionApproval,
    MissionPlan,
    MissionStatus,
    OperationScope,
    utcnow,
    validate_safe_mapping,
)

TRANSITIONS: dict[MissionStatus, frozenset[MissionStatus]] = {
    MissionStatus.DRAFT: frozenset({MissionStatus.PLANNED, MissionStatus.CANCELLED}),
    MissionStatus.PLANNED: frozenset({MissionStatus.APPROVED, MissionStatus.CANCELLED}),
    MissionStatus.APPROVED: frozenset({MissionStatus.READY, MissionStatus.CANCELLED}),
    MissionStatus.READY: frozenset({MissionStatus.RUNNING, MissionStatus.CANCELLED}),
    MissionStatus.RUNNING: frozenset(
        {
            MissionStatus.PAUSED,
            MissionStatus.RECOVERING,
            MissionStatus.COMPLETED,
            MissionStatus.CANCELLED,
        }
    ),
    MissionStatus.PAUSED: frozenset(
        {MissionStatus.RUNNING, MissionStatus.RECOVERING, MissionStatus.CANCELLED}
    ),
    MissionStatus.RECOVERING: frozenset(
        {MissionStatus.RUNNING, MissionStatus.PAUSED, MissionStatus.CANCELLED}
    ),
    MissionStatus.COMPLETED: frozenset({MissionStatus.ARCHIVED}),
    MissionStatus.CANCELLED: frozenset({MissionStatus.ARCHIVED}),
    MissionStatus.ARCHIVED: frozenset({MissionStatus.DELETED}),
    MissionStatus.DELETED: frozenset(),
}


class TikTokAutonomousOperationCenter:
    """Coordinates approved missions without bypass or direct platform automation."""

    def __init__(
        self, delegates: Mapping[str, MissionDelegationPort] | None = None
    ) -> None:
        self.delegates = {
            name: (delegates or {}).get(name, ReferenceOnlyPort(name))
            for name in DELEGATION_MODULES
        }
        self.missions: dict[str, Mission] = {}
        self.plans: dict[str, MissionPlan] = {}
        self.approvals: dict[str, MissionApproval] = {}
        self.executions: dict[str, ExecutionState] = {}
        self.history: list[AuditEntry] = []
        self.metrics = AutonomousMetrics()

    @staticmethod
    def _require(scope: OperationScope, action: str) -> None:
        permission = f"tiktok:autonomous:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:autonomous:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: OperationScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _mission(self, reference: str, scope: OperationScope) -> Mission:
        mission = self.missions[reference]
        self._scoped(mission, scope)
        return mission

    def _record(self, mission: Mission, scope: OperationScope, action: str) -> None:
        validate_safe_mapping({"action": action})
        self.history.append(
            AuditEntry(
                mission.id, mission.tenant, mission.workspace, scope.actor, action
            )
        )

    def create_mission(self, mission: Mission, scope: OperationScope) -> Mission:
        self._require(scope, "write")
        self._scoped(mission, scope)
        mission.validate()
        if mission.id in self.missions:
            raise ValueError("Mission ID must be unique.")
        self.missions[mission.id] = mission
        self.metrics.increment("tiktok_autonomous_missions_total")
        self._record(mission, scope, "mission.created")
        return mission

    def add_plan(self, plan: MissionPlan, scope: OperationScope) -> MissionPlan:
        self._require(scope, "write")
        self._scoped(plan, scope)
        mission = self._mission(plan.mission_id, scope)
        if mission.status is not MissionStatus.DRAFT:
            raise ValueError("Only draft missions accept plans.")
        if (
            not plan.task_references
            or not plan.checkpoint
            or not plan.rollback_reference
        ):
            raise ValueError(
                "Plans require tasks, a checkpoint, and rollback reference."
            )
        validate_safe_mapping(plan.metadata)
        self.plans[plan.id] = plan
        self.transition(mission.id, MissionStatus.PLANNED, scope)
        return plan

    def approve(
        self, approval: MissionApproval, scope: OperationScope
    ) -> MissionApproval:
        self._require(scope, "approve")
        self._scoped(approval, scope)
        mission = self._mission(approval.mission_id, scope)
        if mission.status is not MissionStatus.PLANNED:
            raise ValueError("Only planned missions may be approved.")
        if not approval.approved or approval.expires_at <= utcnow():
            raise ValueError("A current affirmative approval is required.")
        self.approvals[approval.id] = approval
        self.transition(mission.id, MissionStatus.APPROVED, scope)
        self._record(mission, scope, "approval.enforced")
        return approval

    def transition(
        self, reference: str, status: MissionStatus, scope: OperationScope
    ) -> Mission:
        self._require(scope, "write")
        mission = self._mission(reference, scope)
        if status not in TRANSITIONS[mission.status]:
            raise ValueError(
                f"Invalid mission transition: {mission.status.value} -> {status.value}"
            )
        mission.status = status
        mission.updated_at = utcnow()
        if status is MissionStatus.COMPLETED:
            self.metrics.increment("tiktok_autonomous_success")
        self._record(mission, scope, f"mission.transition.{status.value}")
        return mission

    def ready(self, reference: str, scope: OperationScope) -> Mission:
        mission = self._mission(reference, scope)
        valid = any(
            approval.mission_id == reference
            and approval.approved
            and approval.expires_at > utcnow()
            and approval.tenant == scope.tenant
            and approval.workspace == scope.workspace
            for approval in self.approvals.values()
        )
        if not valid:
            raise PermissionError("Current mission approval required.")
        return self.transition(mission.id, MissionStatus.READY, scope)

    def _plan_for(self, mission_id: str, scope: OperationScope) -> MissionPlan:
        plans = [
            plan
            for plan in self.plans.values()
            if plan.mission_id == mission_id
            and plan.tenant == scope.tenant
            and plan.workspace == scope.workspace
        ]
        if not plans:
            raise ValueError("Mission plan required.")
        return plans[-1]

    def _health(self, mission: Mission, scope: OperationScope) -> dict[str, Any]:
        health = {
            name: port.health(mission.id, scope)
            for name, port in self.delegates.items()
        }
        if any(
            bool(value.get("restriction_unresolved"))
            or bool(value.get("challenge_unresolved"))
            for value in health.values()
        ):
            raise PermissionError(
                "Unresolved TikTok restriction or challenge stops execution."
            )
        if any(not bool(value.get("healthy", False)) for value in health.values()):
            raise RuntimeError("Required execution module is unhealthy.")
        return health

    def dispatch(self, reference: str, scope: OperationScope) -> ExecutionState:
        self._require(scope, "execute")
        started = perf_counter()
        mission = self._mission(reference, scope)
        if mission.status is not MissionStatus.READY:
            raise ValueError("Mission must be ready before dispatch.")
        self._health(mission, scope)
        plan = self._plan_for(reference, scope)
        delegated = {
            name: port.dispatch(mission, plan, scope)
            for name, port in self.delegates.items()
        }
        execution = ExecutionState(
            mission.id, mission.tenant, mission.workspace, delegated, plan.checkpoint
        )
        self.executions[reference] = execution
        self.transition(reference, MissionStatus.RUNNING, scope)
        self.metrics.increment("tiktok_autonomous_running")
        self.metrics.set("tiktok_autonomous_latency_seconds", perf_counter() - started)
        self._record(mission, scope, "execution.delegated")
        return execution

    def monitor(self, reference: str, scope: OperationScope) -> dict[str, Any]:
        self._require(scope, "read")
        mission = self._mission(reference, scope)
        execution = self.executions.get(reference)
        health = self._health(mission, scope)
        usage = [
            float(value.get("resource_usage", 0.0)) for value in health.values()
        ]
        return {
            "mission_health": "healthy",
            "mission_progress": execution.progress if execution else 0.0,
            "resource_usage": sum(usage),
            "runtime_state": execution.runtime_state if execution else "pending",
            "queue_state": execution.queue_state if execution else "pending",
            "risk_state": execution.risk_state if execution else "clear",
            "recovery_state": execution.recovery_state if execution else "idle",
        }

    def checkpoint(
        self, reference: str, checkpoint: str, scope: OperationScope
    ) -> ExecutionState:
        self._require(scope, "execute")
        execution = self.executions[reference]
        self._scoped(execution, scope)
        execution.checkpoint = checkpoint
        self._record(self._mission(reference, scope), scope, "execution.checkpoint")
        return execution

    def pause(self, reference: str, scope: OperationScope) -> Mission:
        self._require(scope, "execute")
        mission = self._mission(reference, scope)
        for port in self.delegates.values():
            port.pause(reference, scope)
        self.metrics.set(
            "tiktok_autonomous_running",
            max(0, self.metrics.values["tiktok_autonomous_running"] - 1),
        )
        return self.transition(mission.id, MissionStatus.PAUSED, scope)

    def resume(self, reference: str, scope: OperationScope) -> ExecutionState:
        self._require(scope, "execute")
        mission = self._mission(reference, scope)
        if mission.status not in {MissionStatus.PAUSED, MissionStatus.RECOVERING}:
            raise ValueError("Only paused or recovering missions may resume.")
        self._health(mission, scope)
        execution = self.executions[reference]
        execution.delegated_references.update(
            {
                name: port.resume(reference, execution.checkpoint, scope)
                for name, port in self.delegates.items()
            }
        )
        execution.recovery_state = "resumed"
        self.transition(reference, MissionStatus.RUNNING, scope)
        self.metrics.increment("tiktok_autonomous_running")
        return execution

    def recover(self, reference: str, scope: OperationScope) -> ExecutionState:
        self._require(scope, "recover")
        mission = self._mission(reference, scope)
        if mission.status not in {MissionStatus.RUNNING, MissionStatus.PAUSED}:
            raise ValueError("Only active missions may recover.")
        self._health(mission, scope)
        if mission.status is MissionStatus.RUNNING:
            self.transition(reference, MissionStatus.RECOVERING, scope)
        else:
            mission.status = MissionStatus.RECOVERING
            self._record(mission, scope, "mission.transition.recovering")
        execution = self.executions[reference]
        execution.recovery_state = "recovering"
        self.metrics.increment("tiktok_autonomous_recoveries")
        return execution

    def rollback(self, reference: str, scope: OperationScope) -> Mission:
        self._require(scope, "recover")
        mission = self._mission(reference, scope)
        plan = self._plan_for(reference, scope)
        for port in self.delegates.values():
            port.rollback(reference, plan.rollback_reference, scope)
        self._record(mission, scope, "execution.rollback")
        return self.pause(reference, scope)

    def complete(self, reference: str, scope: OperationScope) -> Mission:
        mission = self.transition(reference, MissionStatus.COMPLETED, scope)
        execution = self.executions[reference]
        execution.progress = 1.0
        execution.finished_at = utcnow()
        self.metrics.set(
            "tiktok_autonomous_running",
            max(0, self.metrics.values["tiktok_autonomous_running"] - 1),
        )
        return mission

    def fail(self, reference: str, scope: OperationScope) -> Mission:
        self.metrics.increment("tiktok_autonomous_failures")
        return self.pause(reference, scope)

    def scoped_values(self, values: Any, scope: OperationScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def analytics(self, scope: OperationScope) -> dict[str, float]:
        self._require(scope, "read")
        missions = self.scoped_values(self.missions.values(), scope)
        completed = sum(item.status is MissionStatus.COMPLETED for item in missions)
        failed = self.metrics.values["tiktok_autonomous_failures"]
        runtimes = [
            (item.finished_at - item.started_at).total_seconds()
            for item in self.scoped_values(self.executions.values(), scope)
            if item.finished_at is not None
        ]
        return {
            "mission_count": float(len(missions)),
            "mission_success": float(completed),
            "mission_failure": failed,
            "mission_runtime": sum(runtimes) / len(runtimes) if runtimes else 0.0,
            "mission_recovery": self.metrics.values[
                "tiktok_autonomous_recoveries"
            ],
            "mission_utilization": (
                sum(
                    self.monitor(item.id, scope)["resource_usage"]
                    for item in missions
                    if item.status is not MissionStatus.DELETED
                )
                / len(missions)
                if missions
                else 0.0
            ),
        }

    def dashboard(self, scope: OperationScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "title": "TikTok Autonomous Operation Center",
            "sections": (
                "Mission Overview",
                "Plans",
                "Objectives",
                "Policies",
                "Constraints",
                "Execution",
                "Monitoring",
                "Recovery",
                "Analytics",
            ),
            "missions": [
                mission.to_dict()
                for mission in self.scoped_values(self.missions.values(), scope)
            ],
            "plans": [
                asdict(plan)
                for plan in self.scoped_values(self.plans.values(), scope)
            ],
            "analytics": self.analytics(scope),
        }
