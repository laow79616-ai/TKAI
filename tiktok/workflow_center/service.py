"""Tenant-isolated workflow lifecycle, scheduling, execution, and audit service."""

from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
from time import perf_counter
from typing import Any

from .adapters import NullWorkflowNodePort, WorkflowNodePort
from .metrics import WorkflowMetrics
from .models import (
    Approval,
    ApprovalKind,
    ApprovalStatus,
    ExecutionStatus,
    HistoryEntry,
    NodeKind,
    StepResult,
    Workflow,
    WorkflowCondition,
    WorkflowExecution,
    WorkflowSchedule,
    WorkflowScope,
    WorkflowStatus,
    WorkflowTemplate,
    utcnow,
)


class TikTokWorkflowOrchestrationCenter:
    """Coordinates approved TikTok operations without bypassing platform controls."""

    def __init__(self, ports: dict[NodeKind, WorkflowNodePort] | None = None) -> None:
        null = NullWorkflowNodePort()
        self.ports = {kind: (ports or {}).get(kind, null) for kind in NodeKind}
        self.workflows: dict[str, Workflow] = {}
        self.templates: dict[str, WorkflowTemplate] = {}
        self.executions: dict[str, WorkflowExecution] = {}
        self.schedules: dict[str, WorkflowSchedule] = {}
        self.approvals: dict[str, Approval] = {}
        self.conditions: dict[str, WorkflowCondition] = {}
        self.history: list[HistoryEntry] = []
        self.execution_queue: list[str] = []
        self.retry_queue: list[str] = []
        self.delayed_queue: list[str] = []
        self.metrics = WorkflowMetrics()

    @staticmethod
    def _require(scope: WorkflowScope, action: str) -> None:
        permission = f"tiktok:workflow:{action}"
        if (
            permission not in scope.permissions
            and "tiktok:workflow:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    @staticmethod
    def _scoped(item: Any, scope: WorkflowScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(
        self,
        execution_reference: str,
        event: str,
        state: str,
        scope: WorkflowScope,
        version: int,
        detail: str = "",
    ) -> None:
        self.history.append(
            HistoryEntry(
                execution_reference,
                scope.tenant,
                scope.workspace,
                event,
                state,
                scope.actor,
                version,
                detail=detail,
            )
        )

    def create_workflow(self, workflow: Workflow, scope: WorkflowScope) -> Workflow:
        self._require(scope, "write")
        self._scoped(workflow, scope)
        workflow.validate()
        if workflow.id in self.workflows:
            raise ValueError("Workflow ID must be unique.")
        self.workflows[workflow.id] = workflow
        self.metrics.increment("tiktok_workflows_total")
        self._record(
            workflow.id,
            "workflow.created",
            workflow.status.value,
            scope,
            workflow.version,
        )
        return workflow

    def list_workflows(self, scope: WorkflowScope) -> list[Workflow]:
        self._require(scope, "read")
        return [
            item
            for item in self.workflows.values()
            if item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.status is not WorkflowStatus.DELETED
        ]

    def update_workflow(
        self, reference: str, scope: WorkflowScope, **changes: Any
    ) -> Workflow:
        self._require(scope, "write")
        current = self.workflows[reference]
        self._scoped(current, scope)
        if current.status not in {WorkflowStatus.DRAFT, WorkflowStatus.REVIEW}:
            raise ValueError("Only draft or review workflows can be edited.")
        protected = {"id", "tenant", "workspace", "owner", "version", "status"}
        if protected & changes.keys():
            raise ValueError(
                "Identity, scope, version, and lifecycle are immutable here."
            )
        updated = replace(
            current, **changes, version=current.version + 1, updated_at=utcnow()
        )
        updated.validate()
        self.workflows[reference] = updated
        self._record(
            reference, "workflow.updated", updated.status.value, scope, updated.version
        )
        return updated

    def transition_workflow(
        self, reference: str, status: WorkflowStatus, scope: WorkflowScope
    ) -> Workflow:
        self._require(scope, "write")
        item = self.workflows[reference]
        self._scoped(item, scope)
        allowed = {
            WorkflowStatus.DRAFT: {
                WorkflowStatus.REVIEW,
                WorkflowStatus.ARCHIVED,
                WorkflowStatus.DELETED,
            },
            WorkflowStatus.REVIEW: {WorkflowStatus.DRAFT, WorkflowStatus.APPROVED},
            WorkflowStatus.APPROVED: {WorkflowStatus.READY, WorkflowStatus.ARCHIVED},
            WorkflowStatus.READY: {
                WorkflowStatus.SCHEDULED,
                WorkflowStatus.RUNNING,
                WorkflowStatus.ARCHIVED,
            },
            WorkflowStatus.SCHEDULED: {
                WorkflowStatus.RUNNING,
                WorkflowStatus.PAUSED,
                WorkflowStatus.ARCHIVED,
            },
            WorkflowStatus.RUNNING: {
                WorkflowStatus.PAUSED,
                WorkflowStatus.COMPLETED,
                WorkflowStatus.FAILED,
            },
            WorkflowStatus.PAUSED: {
                WorkflowStatus.READY,
                WorkflowStatus.RUNNING,
                WorkflowStatus.ARCHIVED,
            },
            WorkflowStatus.COMPLETED: {WorkflowStatus.READY, WorkflowStatus.ARCHIVED},
            WorkflowStatus.FAILED: {WorkflowStatus.READY, WorkflowStatus.ARCHIVED},
            WorkflowStatus.ARCHIVED: {WorkflowStatus.DRAFT, WorkflowStatus.DELETED},
            WorkflowStatus.DELETED: set(),
        }
        if status not in allowed[item.status]:
            raise ValueError(
                f"Invalid workflow transition: {item.status.value} -> {status.value}"
            )
        if status is WorkflowStatus.APPROVED:
            self._require_approval(ApprovalKind.WORKFLOW, reference, scope)
        item.status = status
        item.version += 1
        item.updated_at = utcnow()
        self._record(
            reference, "workflow.transition", status.value, scope, item.version
        )
        return item

    def create_template(
        self, template: WorkflowTemplate, scope: WorkflowScope
    ) -> WorkflowTemplate:
        self._require(scope, "write")
        self._scoped(template, scope)
        if not template.id or not template.name or template.version < 1:
            raise ValueError("Valid template identity, name, and version are required.")
        for node in template.nodes:
            node.validate()
        self.templates[template.id] = template
        self._record(template.id, "template.created", "ready", scope, template.version)
        return template

    def create_schedule(
        self, schedule: WorkflowSchedule, scope: WorkflowScope
    ) -> WorkflowSchedule:
        self._require(scope, "schedule")
        self._scoped(schedule, scope)
        schedule.validate()
        workflow = self.workflows[schedule.workflow_reference]
        self._scoped(workflow, scope)
        if workflow.status not in {WorkflowStatus.READY, WorkflowStatus.SCHEDULED}:
            raise ValueError("Only ready or scheduled workflows can be scheduled.")
        self.schedules[schedule.id] = schedule
        if workflow.status is WorkflowStatus.READY:
            workflow.status = WorkflowStatus.SCHEDULED
        self._record(
            schedule.id,
            "schedule.created",
            schedule.kind.value,
            scope,
            workflow.version,
        )
        return schedule

    def request_approval(self, approval: Approval, scope: WorkflowScope) -> Approval:
        self._require(scope, "approve")
        self._scoped(approval, scope)
        if not approval.id or not approval.reviewer or approval.expires_at <= utcnow():
            raise ValueError(
                "Approval ID, reviewer, and future expiration are required."
            )
        self.approvals[approval.id] = approval
        self._record(
            approval.resource_reference,
            "approval.requested",
            approval.status.value,
            scope,
            1,
            approval.kind.value,
        )
        return approval

    def decide_approval(
        self,
        reference: str,
        decision: ApprovalStatus,
        note: str,
        scope: WorkflowScope,
    ) -> Approval:
        self._require(scope, "approve")
        approval = self.approvals[reference]
        self._scoped(approval, scope)
        if approval.status is not ApprovalStatus.PENDING:
            raise ValueError("Approval is already decided.")
        if utcnow() >= approval.expires_at:
            approval.status = ApprovalStatus.EXPIRED
            raise PermissionError("Approval expired.")
        if decision not in {ApprovalStatus.APPROVED, ApprovalStatus.REJECTED}:
            raise ValueError("Decision must be approved or rejected.")
        approval.status, approval.decided_by, approval.decision_note = (
            decision,
            scope.actor,
            note,
        )
        self._record(
            approval.resource_reference, "approval.decided", decision.value, scope, 1
        )
        return approval

    def _require_approval(
        self, kind: ApprovalKind, resource_reference: str, scope: WorkflowScope
    ) -> Approval:
        matches = [
            item
            for item in self.approvals.values()
            if item.kind is kind
            and item.resource_reference == resource_reference
            and item.tenant == scope.tenant
            and item.workspace == scope.workspace
            and item.status is ApprovalStatus.APPROVED
            and item.expires_at > utcnow()
        ]
        if not matches:
            raise PermissionError(f"Valid {kind.value} approval required.")
        return matches[-1]

    def enqueue_execution(
        self, execution: WorkflowExecution, scope: WorkflowScope
    ) -> WorkflowExecution:
        self._require(scope, "execute")
        self._scoped(execution, scope)
        execution.validate()
        workflow = self.workflows[execution.workflow_reference]
        self._scoped(workflow, scope)
        if workflow.status not in {WorkflowStatus.READY, WorkflowStatus.SCHEDULED}:
            raise ValueError("Workflow must be ready or scheduled.")
        if execution.workflow_version != workflow.version:
            raise ValueError("Execution must pin the current workflow version.")
        self._require_approval(ApprovalKind.EXECUTION, execution.id, scope)
        self.executions[execution.id] = execution
        self.execution_queue.append(execution.id)
        self.execution_queue.sort(
            key=lambda ref: self.executions[ref].priority, reverse=True
        )
        self.metrics.increment("tiktok_workflow_executions_total")
        self._record(
            execution.id,
            "execution.queued",
            execution.status.value,
            scope,
            workflow.version,
        )
        return execution

    def execute_next(
        self, scope: WorkflowScope, context: dict[str, Any] | None = None
    ) -> WorkflowExecution | None:
        self._require(scope, "execute")
        reference = next(
            (
                ref
                for ref in self.execution_queue
                if self.executions[ref].tenant == scope.tenant
                and self.executions[ref].workspace == scope.workspace
            ),
            None,
        )
        if reference is None:
            return None
        self.execution_queue.remove(reference)
        return self.run_execution(reference, scope, context or {})

    def run_execution(
        self, reference: str, scope: WorkflowScope, context: dict[str, Any]
    ) -> WorkflowExecution:
        started = perf_counter()
        execution = self.executions[reference]
        self._scoped(execution, scope)
        workflow = self.workflows[execution.workflow_reference]
        execution.status, execution.started_at = ExecutionStatus.RUNNING, utcnow()
        self._record(
            reference,
            "execution.started",
            execution.status.value,
            scope,
            workflow.version,
        )
        try:
            for index, node in enumerate(
                workflow.nodes[execution.checkpoint :], execution.checkpoint
            ):
                if execution.cancellation_requested:
                    execution.status = ExecutionStatus.CANCELLED
                    break
                if node.high_risk or node.kind is NodeKind.MANUAL_APPROVAL:
                    self._require_approval(
                        ApprovalKind.HIGH_RISK_STEP, f"{reference}:{node.id}", scope
                    )
                condition_ref = next(
                    (
                        edge.condition_reference
                        for edge in workflow.edges
                        if edge.target == node.id and edge.condition_reference
                    ),
                    "",
                )
                if condition_ref and not self.conditions[condition_ref].evaluate(
                    context
                ):
                    continue
                node_started = perf_counter()
                attempt = 0
                while True:
                    attempt += 1
                    try:
                        output = self.ports[node.kind].execute(
                            node.name,
                            {"reference": reference, **node.configuration},
                            scope,
                        )
                        execution.results.append(
                            StepResult(
                                node.id,
                                ExecutionStatus.COMPLETED,
                                attempt,
                                perf_counter() - node_started,
                                output,
                            )
                        )
                        execution.checkpoint = index + 1
                        break
                    except Exception as error:
                        if attempt > node.maximum_retries:
                            execution.results.append(
                                StepResult(
                                    node.id,
                                    ExecutionStatus.FAILED,
                                    attempt,
                                    perf_counter() - node_started,
                                    error=str(error),
                                )
                            )
                            raise
                        execution.retry_count += 1
                        self.metrics.increment("tiktok_workflow_retry_total")
            if execution.status is ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED
                self.metrics.increment("tiktok_workflow_success_total")
        except Exception as error:
            execution.status = ExecutionStatus.FAILED
            self.retry_queue.append(reference)
            self.metrics.increment("tiktok_workflow_failures_total")
            self._record(
                reference,
                "execution.failed",
                execution.status.value,
                scope,
                workflow.version,
                str(error),
            )
        execution.finished_at = utcnow()
        self.metrics.set("tiktok_workflow_latency_seconds", perf_counter() - started)
        self._record(
            reference,
            "execution.finished",
            execution.status.value,
            scope,
            workflow.version,
        )
        return execution

    def pause(self, reference: str, scope: WorkflowScope) -> WorkflowExecution:
        execution = self.executions[reference]
        self._scoped(execution, scope)
        if execution.status is not ExecutionStatus.RUNNING:
            raise ValueError("Only a running execution can be paused.")
        execution.status = ExecutionStatus.PAUSED
        self._record(
            reference,
            "execution.paused",
            execution.status.value,
            scope,
            execution.workflow_version,
        )
        return execution

    def resume(
        self,
        reference: str,
        scope: WorkflowScope,
        context: dict[str, Any] | None = None,
    ) -> WorkflowExecution:
        execution = self.executions[reference]
        self._scoped(execution, scope)
        if execution.status not in {ExecutionStatus.PAUSED, ExecutionStatus.FAILED}:
            raise ValueError("Only paused or failed executions can resume.")
        execution.status = ExecutionStatus.QUEUED
        return self.run_execution(reference, scope, context or {})

    def cancel(self, reference: str, scope: WorkflowScope) -> WorkflowExecution:
        self._require(scope, "execute")
        execution = self.executions[reference]
        self._scoped(execution, scope)
        execution.cancellation_requested = True
        if execution.status is ExecutionStatus.QUEUED:
            execution.status = ExecutionStatus.CANCELLED
            if reference in self.execution_queue:
                self.execution_queue.remove(reference)
        self._record(
            reference,
            "execution.cancelled",
            execution.status.value,
            scope,
            execution.workflow_version,
        )
        return execution

    def rollback(self, reference: str, scope: WorkflowScope) -> WorkflowExecution:
        self._require(scope, "execute")
        execution = self.executions[reference]
        self._scoped(execution, scope)
        workflow = self.workflows[execution.workflow_reference]
        nodes = {node.id: node for node in workflow.nodes}
        for result in reversed(execution.results):
            if result.status is ExecutionStatus.COMPLETED:
                node = nodes[result.node_reference]
                self.ports[node.kind].rollback(node.name, result.output, scope)
        execution.status = ExecutionStatus.ROLLED_BACK
        self._record(
            reference,
            "execution.rolled_back",
            execution.status.value,
            scope,
            workflow.version,
        )
        return execution

    def expire_approvals(self, scope: WorkflowScope) -> int:
        self._require(scope, "approve")
        expired = 0
        for item in self.approvals.values():
            if (
                item.tenant == scope.tenant
                and item.workspace == scope.workspace
                and item.status is ApprovalStatus.PENDING
                and item.expires_at <= utcnow()
            ):
                item.status = ApprovalStatus.EXPIRED
                expired += 1
        return expired

    def analytics(self, scope: WorkflowScope) -> dict[str, float | int]:
        self._require(scope, "read")
        values = [
            item
            for item in self.executions.values()
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]
        completed = [
            item for item in values if item.status is ExecutionStatus.COMPLETED
        ]
        failed = [item for item in values if item.status is ExecutionStatus.FAILED]
        durations = [
            (item.finished_at - item.started_at).total_seconds()
            for item in values
            if item.started_at and item.finished_at
        ]
        step_durations = [
            result.duration_seconds for item in values for result in item.results
        ]
        total = len(values)
        return {
            "workflow_runs": total,
            "success_rate": len(completed) / total if total else 0,
            "failure_rate": len(failed) / total if total else 0,
            "average_runtime": sum(durations) / len(durations) if durations else 0,
            "retry_count": sum(item.retry_count for item in values),
            "queue_time": sum(item.queue_time_seconds for item in values) / total
            if total
            else 0,
            "average_step_duration": sum(step_durations) / len(step_durations)
            if step_durations
            else 0,
        }

    def queue_metrics(self, scope: WorkflowScope) -> dict[str, int]:
        self._require(scope, "read")

        def in_scope(reference: str) -> bool:
            return (
                self.executions[reference].tenant == scope.tenant
                and self.executions[reference].workspace == scope.workspace
            )

        return {
            "execution_queue": sum(map(in_scope, self.execution_queue)),
            "priority_queue": sum(map(in_scope, self.execution_queue)),
            "retry_queue": sum(map(in_scope, self.retry_queue)),
            "delayed_queue": sum(map(in_scope, self.delayed_queue)),
            "running": sum(
                item.status is ExecutionStatus.RUNNING
                for item in self.executions.values()
                if item.tenant == scope.tenant and item.workspace == scope.workspace
            ),
        }

    def dashboard(self, scope: WorkflowScope) -> dict[str, Any]:
        self._require(scope, "read")
        return {
            "sections": (
                "Workflow Designer",
                "Templates",
                "Executions",
                "Queues",
                "Schedules",
                "Approvals",
                "History",
                "Analytics",
                "Statistics",
            ),
            "statistics": self.analytics(scope),
            "queues": self.queue_metrics(scope),
            "pending_approvals": sum(
                item.status is ApprovalStatus.PENDING
                for item in self.approvals.values()
                if item.tenant == scope.tenant and item.workspace == scope.workspace
            ),
        }

    def create_execution_approval(
        self, execution_reference: str, reviewer: str, scope: WorkflowScope
    ) -> Approval:
        return self.request_approval(
            Approval(
                f"approval-{execution_reference}",
                scope.tenant,
                scope.workspace,
                ApprovalKind.EXECUTION,
                execution_reference,
                reviewer,
                utcnow() + timedelta(hours=1),
            ),
            scope,
        )
