"""Enterprise local TikTok Automation Engine."""

from __future__ import annotations

from dataclasses import replace
from time import perf_counter
from typing import Any

from .adapters import AutomationPort, LocalMockPort
from .metrics import AutomationMetrics
from .models import (
    AuditEvent,
    Automation,
    AutomationApproval,
    AutomationCondition,
    AutomationExecution,
    AutomationPlan,
    AutomationScope,
    AutomationStatus,
    AutomationTemplate,
    AutomationTrigger,
    ExecutionStatus,
    QueueKind,
    utcnow,
)

TRANSITIONS = {
    AutomationStatus.DRAFT: {AutomationStatus.REVIEW, AutomationStatus.DELETED},
    AutomationStatus.REVIEW: {AutomationStatus.DRAFT, AutomationStatus.APPROVED},
    AutomationStatus.APPROVED: {AutomationStatus.READY, AutomationStatus.ARCHIVED},
    AutomationStatus.READY: {
        AutomationStatus.SCHEDULED,
        AutomationStatus.RUNNING,
        AutomationStatus.ARCHIVED,
    },
    AutomationStatus.SCHEDULED: {
        AutomationStatus.RUNNING,
        AutomationStatus.PAUSED,
    },
    AutomationStatus.RUNNING: {
        AutomationStatus.PAUSED,
        AutomationStatus.COMPLETED,
        AutomationStatus.FAILED,
    },
    AutomationStatus.PAUSED: {
        AutomationStatus.READY,
        AutomationStatus.RUNNING,
        AutomationStatus.ARCHIVED,
    },
    AutomationStatus.COMPLETED: {AutomationStatus.READY, AutomationStatus.ARCHIVED},
    AutomationStatus.FAILED: {AutomationStatus.READY, AutomationStatus.ARCHIVED},
    AutomationStatus.ARCHIVED: {AutomationStatus.DELETED},
    AutomationStatus.DELETED: set(),
}


class TikTokAutomationEngine:
    """Coordinates approved bounded workflows without platform-control bypass."""

    def __init__(self, port: AutomationPort | None = None) -> None:
        self.port = port or LocalMockPort()
        self.automations: dict[str, Automation] = {}
        self.plans: dict[str, AutomationPlan] = {}
        self.templates: dict[str, AutomationTemplate] = {}
        self.executions: dict[str, AutomationExecution] = {}
        self.triggers: dict[str, AutomationTrigger] = {}
        self.conditions: dict[str, AutomationCondition] = {}
        self.approvals: dict[str, AutomationApproval] = {}
        self.queues: dict[QueueKind, list[str]] = {kind: [] for kind in QueueKind}
        self.audit: list[AuditEvent] = []
        self.metrics = AutomationMetrics()

    @staticmethod
    def _require(scope: AutomationScope, action: str) -> None:
        needed = f"tiktok:automation:{action}"
        if (
            needed not in scope.permissions
            and "tiktok:automation:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {needed}")

    @staticmethod
    def _scoped(item: Any, scope: AutomationScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(
        self,
        reference: str,
        event: str,
        state: str,
        scope: AutomationScope,
        detail: str = "",
    ) -> None:
        self.audit.append(
            AuditEvent(
                reference,
                scope.tenant,
                scope.workspace,
                event,
                state,
                scope.actor,
                detail,
            )
        )

    def create_automation(
        self, automation: Automation, scope: AutomationScope
    ) -> Automation:
        self._require(scope, "write")
        self._scoped(automation, scope)
        automation.validate()
        if automation.id in self.automations:
            raise ValueError("Automation ID must be unique.")
        self.automations[automation.id] = automation
        self.metrics.increment("tiktok_automation_total")
        self._record(
            automation.id, "automation.created", automation.status.value, scope
        )
        return automation

    def list_automations(self, scope: AutomationScope) -> list[Automation]:
        self._require(scope, "read")
        return [
            item
            for item in self.automations.values()
            if item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.status is not AutomationStatus.DELETED
        ]

    def update_automation(
        self, reference: str, scope: AutomationScope, **changes: Any
    ) -> Automation:
        self._require(scope, "write")
        current = self.automations[reference]
        self._scoped(current, scope)
        if current.status not in {AutomationStatus.DRAFT, AutomationStatus.REVIEW}:
            raise ValueError("Only draft or review automations can be edited.")
        protected = {"id", "tenant", "workspace", "owner", "version", "status"}
        if protected & changes.keys():
            raise ValueError(
                "Identity, scope, version, and lifecycle are immutable here."
            )
        updated = replace(
            current, **changes, version=current.version + 1, updated_at=utcnow()
        )
        updated.validate()
        self.automations[reference] = updated
        self._record(reference, "automation.updated", updated.status.value, scope)
        return updated

    def transition(
        self, reference: str, status: AutomationStatus, scope: AutomationScope
    ) -> Automation:
        self._require(scope, "write")
        item = self.automations[reference]
        self._scoped(item, scope)
        if status not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid automation transition: {item.status.value} -> {status.value}"
            )
        if status is AutomationStatus.APPROVED:
            self._require(scope, "approve")
            approval = self.approvals.get(reference)
            if approval is None or not approval.approved:
                raise PermissionError("Approved review is required.")
        item.status = status
        item.updated_at = utcnow()
        self._record(reference, "automation.transitioned", status.value, scope)
        return item

    def create_plan(
        self, plan: AutomationPlan, scope: AutomationScope
    ) -> AutomationPlan:
        self._require(scope, "write")
        self._scoped(plan, scope)
        plan.validate()
        self.plans[plan.id] = plan
        return plan

    def create_template(
        self, template: AutomationTemplate, scope: AutomationScope
    ) -> AutomationTemplate:
        self._require(scope, "write")
        self._scoped(template, scope)
        if template.plan_reference not in self.plans:
            raise ValueError("Template plan does not exist.")
        self.templates[template.id] = template
        return template

    def create_trigger(
        self, trigger: AutomationTrigger, scope: AutomationScope
    ) -> AutomationTrigger:
        self._require(scope, "write")
        self._scoped(trigger, scope)
        trigger.validate()
        self.triggers[trigger.id] = trigger
        return trigger

    def create_condition(
        self, condition: AutomationCondition, scope: AutomationScope
    ) -> AutomationCondition:
        self._require(scope, "write")
        self._scoped(condition, scope)
        self.conditions[condition.id] = condition
        return condition

    def approve(
        self, approval: AutomationApproval, scope: AutomationScope
    ) -> AutomationApproval:
        self._require(scope, "approve")
        self._scoped(approval, scope)
        approval.approved = True
        approval.decided_by = scope.actor
        self.approvals[approval.automation_reference] = approval
        self._record(
            approval.automation_reference, "automation.approved", "approved", scope
        )
        return approval

    def enqueue(
        self,
        execution: AutomationExecution,
        scope: AutomationScope,
        queue: QueueKind = QueueKind.EXECUTION,
    ) -> AutomationExecution:
        self._require(scope, "execute")
        self._scoped(execution, scope)
        execution.validate()
        automation = self.automations[execution.automation_reference]
        plan = self.plans[execution.plan_reference]
        self._scoped(automation, scope)
        self._scoped(plan, scope)
        if automation.status not in {
            AutomationStatus.READY,
            AutomationStatus.SCHEDULED,
        }:
            raise ValueError("Automation must be ready or scheduled.")
        if (
            plan.approval_required
            and not self.approvals.get(
                automation.id,
                AutomationApproval(
                    "", scope.tenant, scope.workspace, automation.id, ""
                ),
            ).approved
        ):
            raise PermissionError("Execution approval is required.")
        running = sum(
            item.status is ExecutionStatus.RUNNING
            for item in self.executions.values()
            if item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.plan_reference == plan.id
        )
        if running >= plan.maximum_concurrency:
            queue = QueueKind.DELAYED
        self.executions[execution.id] = execution
        target = QueueKind.PRIORITY if execution.priority > 50 else queue
        self.queues[target].append(execution.id)
        self.queues[target].sort(
            key=lambda ref: self.executions[ref].priority, reverse=True
        )
        self._record(execution.id, "execution.enqueued", target.value, scope)
        return execution

    def execute_next(
        self, scope: AutomationScope, context: dict[str, Any] | None = None
    ) -> AutomationExecution | None:
        self._require(scope, "execute")
        for kind in (
            QueueKind.PRIORITY,
            QueueKind.EXECUTION,
            QueueKind.RETRY,
            QueueKind.RECOVERY,
        ):
            for reference in list(self.queues[kind]):
                item = self.executions[reference]
                if item.tenant == scope.tenant and item.workspace == scope.workspace:
                    self.queues[kind].remove(reference)
                    return self.run(reference, scope, context or {})
        return None

    def run(
        self, reference: str, scope: AutomationScope, context: dict[str, Any]
    ) -> AutomationExecution:
        execution = self.executions[reference]
        self._scoped(execution, scope)
        plan = self.plans[execution.plan_reference]
        started = perf_counter()
        execution.status = ExecutionStatus.RUNNING
        execution.started_at = execution.started_at or utcnow()
        self.metrics.set("tiktok_automation_running", 1)
        self._record(reference, "execution.started", "running", scope)
        try:
            for index, step in enumerate(
                execution.steps[execution.checkpoint :], execution.checkpoint
            ):
                if execution.graceful_stop_requested:
                    execution.status = ExecutionStatus.STOPPED
                    break
                if step.condition_reference and not self.conditions[
                    step.condition_reference
                ].evaluate(context):
                    continue
                health = self.port.health(step.module, scope)
                if health.get("restriction_unresolved"):
                    execution.restriction_unresolved = True
                    execution.status = ExecutionStatus.BLOCKED
                    execution.last_error = "Unresolved TikTok restriction or challenge."
                    break
                if not health.get("healthy", False):
                    raise RuntimeError(f"{step.module} is unhealthy")
                attempts = 0
                while True:
                    attempts += 1
                    try:
                        self.port.execute(
                            step.module, step.action, step.configuration, scope
                        )
                        if step.checkpoint:
                            execution.checkpoint = index + 1
                        break
                    except Exception:
                        if attempts >= plan.maximum_attempts:
                            raise
                        execution.retry_count += 1
                        self.metrics.increment("tiktok_automation_retries")
            if execution.status is ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED
                self.metrics.increment("tiktok_automation_success")
        except Exception as error:
            execution.status = ExecutionStatus.FAILED
            execution.last_error = str(error)
            self.queues[QueueKind.RETRY].append(reference)
            self.metrics.increment("tiktok_automation_failures")
        execution.finished_at = utcnow()
        self.metrics.set("tiktok_automation_running", 0)
        self.metrics.set(
            "tiktok_automation_execution_seconds", perf_counter() - started
        )
        self._record(
            reference,
            "execution.finished",
            execution.status.value,
            scope,
            execution.last_error,
        )
        return execution

    def pause(self, reference: str, scope: AutomationScope) -> AutomationExecution:
        item = self.executions[reference]
        self._scoped(item, scope)
        if item.status is not ExecutionStatus.RUNNING:
            raise ValueError("Only running execution can pause.")
        item.status = ExecutionStatus.PAUSED
        return item

    def graceful_stop(
        self, reference: str, scope: AutomationScope
    ) -> AutomationExecution:
        self._require(scope, "execute")
        item = self.executions[reference]
        self._scoped(item, scope)
        item.graceful_stop_requested = True
        if item.status is ExecutionStatus.QUEUED:
            item.status = ExecutionStatus.STOPPED
        return item

    def recover(self, reference: str, scope: AutomationScope) -> AutomationExecution:
        self._require(scope, "recover")
        item = self.executions[reference]
        self._scoped(item, scope)
        plan = self.plans[item.plan_reference]
        if item.restriction_unresolved:
            item.status = ExecutionStatus.BLOCKED
            raise PermissionError(
                "Recovery stopped: unresolved TikTok restriction or challenge."
            )
        if item.recovery_count >= plan.maximum_attempts:
            raise ValueError("Maximum recovery attempts reached.")
        item.recovery_count += 1
        item.status = ExecutionStatus.QUEUED
        self.queues[QueueKind.RECOVERY].append(reference)
        self.metrics.increment("tiktok_automation_recoveries")
        self._record(reference, "execution.recovery.queued", "queued", scope)
        return item

    def rollback(self, reference: str, scope: AutomationScope) -> AutomationExecution:
        self._require(scope, "execute")
        item = self.executions[reference]
        self._scoped(item, scope)
        for step in reversed(item.steps[: item.checkpoint]):
            if step.rollback_action:
                self.port.rollback(
                    step.module, step.rollback_action, step.configuration, scope
                )
        item.status = ExecutionStatus.ROLLED_BACK
        self._record(reference, "execution.rolled_back", "rolled_back", scope)
        return item

    def queue_health(self, scope: AutomationScope) -> dict[str, int]:
        self._require(scope, "read")
        return {
            kind.value: sum(
                self.executions[ref].tenant == scope.tenant
                and self.executions[ref].workspace == scope.workspace
                for ref in values
            )
            for kind, values in self.queues.items()
        }

    def analytics(self, scope: AutomationScope) -> dict[str, float | int]:
        self._require(scope, "read")
        values = [
            item
            for item in self.executions.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]
        total = len(values)

        def count(status: ExecutionStatus) -> int:
            return sum(item.status is status for item in values)

        durations = [
            (item.finished_at - item.started_at).total_seconds()
            for item in values
            if item.started_at and item.finished_at
        ]
        return {
            "execution_count": total,
            "success_rate": count(ExecutionStatus.COMPLETED) / total if total else 0,
            "failure_rate": count(ExecutionStatus.FAILED) / total if total else 0,
            "retry_rate": sum(item.retry_count for item in values) / total
            if total
            else 0,
            "recovery_rate": sum(item.recovery_count for item in values) / total
            if total
            else 0,
            "execution_duration": sum(durations) / len(durations) if durations else 0,
        }

    def monitoring(self, scope: AutomationScope) -> dict[str, Any]:
        self._require(scope, "read")
        executions = [
            item
            for item in self.executions.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]
        return {
            "execution_health": "degraded"
            if any(
                item.status in {ExecutionStatus.FAILED, ExecutionStatus.BLOCKED}
                for item in executions
            )
            else "healthy",
            "runtime_health": "healthy",
            "progress": {item.id: item.checkpoint for item in executions},
            "queue_health": self.queue_health(scope),
            "failures": sum(
                item.status is ExecutionStatus.FAILED for item in executions
            ),
            "audit_events": sum(
                event.tenant == scope.tenant and event.workspace == scope.workspace
                for event in self.audit
            ),
        }

    def dashboard(self, scope: AutomationScope) -> dict[str, Any]:
        return {
            "sections": (
                "Automations",
                "Plans",
                "Executions",
                "Triggers",
                "Conditions",
                "Queues",
                "Monitoring",
                "Recovery",
                "Analytics",
            ),
            "analytics": self.analytics(scope),
            "monitoring": self.monitoring(scope),
        }
