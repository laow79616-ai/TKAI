"""Approval-gated orchestration over existing TikTok execution systems."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from .adapters import (
    ExecutionInfrastructurePort,
    LocalMockInfrastructure,
    LocalReferenceVault,
    ReferenceVaultPort,
)
from .metrics import ExecutionMetrics
from .models import (
    AuditEvent,
    Checkpoint,
    ExecutionPipeline,
    ExecutionPlan,
    ExecutionScope,
    ExecutionStage,
    ExecutionStatus,
    PipelineKind,
    StageKind,
    StageStatus,
    StepResult,
    VerificationKind,
    VerificationRecord,
    utcnow,
)

TRANSITIONS: dict[ExecutionStatus, frozenset[ExecutionStatus]] = {
    ExecutionStatus.PENDING: frozenset(
        {ExecutionStatus.VALIDATED, ExecutionStatus.FAILED, ExecutionStatus.ARCHIVED}
    ),
    ExecutionStatus.VALIDATED: frozenset(
        {ExecutionStatus.QUEUED, ExecutionStatus.FAILED}
    ),
    ExecutionStatus.QUEUED: frozenset(
        {ExecutionStatus.DISPATCHING, ExecutionStatus.PAUSED, ExecutionStatus.FAILED}
    ),
    ExecutionStatus.DISPATCHING: frozenset(
        {ExecutionStatus.RUNNING, ExecutionStatus.FAILED}
    ),
    ExecutionStatus.RUNNING: frozenset(
        {
            ExecutionStatus.PAUSED,
            ExecutionStatus.CHECKPOINTED,
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
        }
    ),
    ExecutionStatus.PAUSED: frozenset(
        {ExecutionStatus.QUEUED, ExecutionStatus.RECOVERING, ExecutionStatus.ARCHIVED}
    ),
    ExecutionStatus.CHECKPOINTED: frozenset(
        {
            ExecutionStatus.RUNNING,
            ExecutionStatus.RECOVERING,
            ExecutionStatus.COMPLETED,
            ExecutionStatus.FAILED,
        }
    ),
    ExecutionStatus.RECOVERING: frozenset(
        {ExecutionStatus.QUEUED, ExecutionStatus.FAILED, ExecutionStatus.ROLLED_BACK}
    ),
    ExecutionStatus.COMPLETED: frozenset({ExecutionStatus.ARCHIVED}),
    ExecutionStatus.FAILED: frozenset(
        {
            ExecutionStatus.RECOVERING,
            ExecutionStatus.ROLLED_BACK,
            ExecutionStatus.ARCHIVED,
        }
    ),
    ExecutionStatus.ROLLED_BACK: frozenset({ExecutionStatus.ARCHIVED}),
    ExecutionStatus.ARCHIVED: frozenset({ExecutionStatus.DELETED}),
    ExecutionStatus.DELETED: frozenset(),
}


class TikTokAIExecutionEngine:
    """Executes only approved, bounded plans through injected infrastructure ports."""

    def __init__(
        self,
        infrastructure: ExecutionInfrastructurePort | None = None,
        vault: ReferenceVaultPort | None = None,
    ) -> None:
        self.infrastructure = infrastructure or LocalMockInfrastructure()
        self.vault = vault or LocalReferenceVault()
        self.plans: dict[str, ExecutionPlan] = {}
        self.pipelines: dict[str, ExecutionPipeline] = {}
        self.stages: dict[str, ExecutionStage] = {}
        self.checkpoints: dict[str, Checkpoint] = {}
        self.results: dict[str, StepResult] = {}
        self.verifications: dict[str, VerificationRecord] = {}
        self.audit: list[AuditEvent] = []
        self.queue: list[str] = []
        self.workers: dict[str, str] = {}
        self.metrics = ExecutionMetrics()

    @staticmethod
    def _require(scope: ExecutionScope, permission: str) -> None:
        required = f"tiktok:execution:{permission}"
        if (
            required not in scope.permissions
            and "tiktok:execution:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: ExecutionScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def scoped_values(self, values: Any, scope: ExecutionScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def _record(
        self, plan: ExecutionPlan, scope: ExecutionScope, action: str, detail: str = ""
    ) -> None:
        forbidden = ("password=", "secret=", "token=", "cookie=", "session=")
        if any(marker in detail.casefold() for marker in forbidden):
            raise ValueError("Secrets are forbidden in execution audit records.")
        self.audit.append(
            AuditEvent(
                plan.id,
                plan.tenant,
                plan.workspace,
                scope.actor,
                action,
                detail,
            )
        )

    def create_plan(
        self,
        plan: ExecutionPlan,
        pipeline: ExecutionPipeline,
        scope: ExecutionScope,
    ) -> ExecutionPlan:
        self._require(scope, "write")
        self._scoped(plan, scope)
        self._scoped(pipeline, scope)
        plan.validate()
        pipeline.validate()
        if pipeline.execution_id != plan.id:
            raise ValueError("Pipeline must belong to the execution plan.")
        if plan.id in self.plans or pipeline.id in self.pipelines:
            raise ValueError("Execution and pipeline IDs must be unique.")
        plan.approved_plan_reference = self.vault.protect(
            plan.approved_plan_reference, scope
        )
        plan.workflow_reference = self.vault.protect(plan.workflow_reference, scope)
        plan.automation_reference = self.vault.protect(plan.automation_reference, scope)
        plan.runtime_reference = self.vault.protect(plan.runtime_reference, scope)
        self.plans[plan.id] = plan
        self.pipelines[pipeline.id] = pipeline
        for kind in StageKind:
            stage = ExecutionStage(
                f"{plan.id}:{kind.value}",
                plan.id,
                plan.tenant,
                plan.workspace,
                kind,
            )
            self.stages[stage.id] = stage
        self.metrics.increment("tiktok_execution_total")
        self._record(plan, scope, "execution.created")
        return plan

    def transition(
        self, execution_id: str, status: ExecutionStatus, scope: ExecutionScope
    ) -> ExecutionPlan:
        self._require(scope, "write")
        plan = self.plans[execution_id]
        self._scoped(plan, scope)
        if status not in TRANSITIONS[plan.status]:
            raise ValueError(
                f"Invalid execution transition: {plan.status.value} -> {status.value}"
            )
        plan.status = status
        plan.version += 1
        plan.updated_at = utcnow()
        self._record(plan, scope, f"execution.transition.{status.value}")
        return plan

    def _stage(
        self,
        plan: ExecutionPlan,
        kind: StageKind,
        status: StageStatus,
        detail: str = "",
    ) -> None:
        stage = self.stages[f"{plan.id}:{kind.value}"]
        stage.status = status
        stage.progress = 100 if status is StageStatus.COMPLETED else stage.progress
        stage.detail = detail

    def validate(self, execution_id: str, scope: ExecutionScope) -> ExecutionPlan:
        self._require(scope, "execute")
        plan = self.plans[execution_id]
        self._scoped(plan, scope)
        if plan.status is not ExecutionStatus.PENDING:
            raise ValueError("Only pending executions may be validated.")
        self._stage(plan, StageKind.VALIDATION, StageStatus.RUNNING)
        failures: list[str] = []
        for kind in VerificationKind:
            passed, detail = self.infrastructure.validate(kind, plan, scope)
            record = VerificationRecord(
                f"{plan.id}:{kind.value}",
                plan.id,
                plan.tenant,
                plan.workspace,
                kind,
                passed,
                detail,
            )
            self.verifications[record.id] = record
            if not passed:
                failures.append(kind.value)
        if failures:
            self._stage(
                plan, StageKind.VALIDATION, StageStatus.FAILED, ",".join(failures)
            )
            self.transition(execution_id, ExecutionStatus.FAILED, scope)
            self.metrics.increment("tiktok_execution_failed")
            raise PermissionError("Execution validation failed: " + ", ".join(failures))
        self._stage(plan, StageKind.VALIDATION, StageStatus.COMPLETED)
        return self.transition(execution_id, ExecutionStatus.VALIDATED, scope)

    def enqueue(self, execution_id: str, scope: ExecutionScope) -> ExecutionPlan:
        plan = self.plans[execution_id]
        self._scoped(plan, scope)
        if plan.status is not ExecutionStatus.VALIDATED:
            raise ValueError("Only validated executions may be queued.")
        self.transition(execution_id, ExecutionStatus.QUEUED, scope)
        self.queue.append(execution_id)
        self._record(plan, scope, "queue.accepted")
        return plan

    def _pipeline(self, execution_id: str) -> ExecutionPipeline:
        return next(
            item
            for item in self.pipelines.values()
            if item.execution_id == execution_id
        )

    def _create_checkpoint(
        self, plan: ExecutionPlan, completed: list[str], scope: ExecutionScope
    ) -> Checkpoint:
        if plan.status is ExecutionStatus.RUNNING:
            self.transition(plan.id, ExecutionStatus.CHECKPOINTED, scope)
        resources = self.infrastructure.checkpoint(plan.id, completed, scope)
        checkpoint = Checkpoint(
            f"checkpoint-{plan.id}-{len(self.checkpoints) + 1}",
            plan.id,
            plan.tenant,
            plan.workspace,
            list(completed),
            [self.vault.protect(item, scope) for item in resources],
            plan.runtime_reference,
        )
        self.checkpoints[checkpoint.id] = checkpoint
        self._record(plan, scope, "checkpoint.created", checkpoint.id)
        if plan.status is ExecutionStatus.CHECKPOINTED:
            self.transition(plan.id, ExecutionStatus.RUNNING, scope)
        return checkpoint

    def dispatch(self, execution_id: str, scope: ExecutionScope) -> ExecutionPlan:
        self._require(scope, "execute")
        plan = self.plans[execution_id]
        self._scoped(plan, scope)
        if plan.status is not ExecutionStatus.QUEUED:
            raise ValueError("Only queued executions may dispatch.")
        started = perf_counter()
        pipeline = self._pipeline(execution_id)
        if execution_id in self.queue:
            self.queue.remove(execution_id)
        self.transition(execution_id, ExecutionStatus.DISPATCHING, scope)
        self._stage(plan, StageKind.PREPARATION, StageStatus.COMPLETED)
        self._stage(plan, StageKind.RESOURCE_ALLOCATION, StageStatus.COMPLETED)
        self._stage(plan, StageKind.DISPATCH, StageStatus.RUNNING)
        self.workers[execution_id] = "existing-scheduler-worker"
        self.transition(execution_id, ExecutionStatus.RUNNING, scope)
        self.metrics.increment("tiktok_execution_running")
        plan.started_at = utcnow()
        self._stage(plan, StageKind.DISPATCH, StageStatus.COMPLETED)
        self._stage(plan, StageKind.EXECUTION, StageStatus.RUNNING)
        completed: list[str] = []
        try:
            for step in pipeline.steps:
                if any(dependency not in completed for dependency in step.depends_on):
                    raise RuntimeError("Step dependency has not completed.")
                if (
                    pipeline.kind is PipelineKind.CONDITIONAL
                    and step.condition == "false"
                ):
                    continue
                result_payload: dict[str, Any] = {}
                error = ""
                attempts = 0
                step_started = perf_counter()
                while attempts < step.maximum_attempts:
                    attempts += 1
                    try:
                        result_payload = self.infrastructure.dispatch(step, scope)
                        if not result_payload.get("accepted", False):
                            raise RuntimeError("Existing infrastructure rejected step.")
                        error = ""
                        break
                    except Exception as exc:
                        error = str(exc)
                success = not error
                result_reference = self.vault.protect(
                    str(result_payload.get("reference", f"failed://{step.id}")), scope
                )
                result = StepResult(
                    f"result-{plan.id}-{step.id}",
                    plan.id,
                    step.id,
                    plan.tenant,
                    plan.workspace,
                    success,
                    result_reference,
                    attempts,
                    perf_counter() - step_started,
                    error,
                )
                self.results[result.id] = result
                if not success:
                    raise RuntimeError(error)
                completed.append(step.id)
                if step.checkpoint_after or pipeline.kind is PipelineKind.CHECKPOINTED:
                    self._create_checkpoint(plan, completed, scope)
            self._stage(plan, StageKind.EXECUTION, StageStatus.COMPLETED)
            self._stage(plan, StageKind.VERIFICATION, StageStatus.COMPLETED)
            self._stage(plan, StageKind.COMPLETION, StageStatus.COMPLETED)
            self.transition(execution_id, ExecutionStatus.COMPLETED, scope)
            plan.finished_at = utcnow()
            self.metrics.increment("tiktok_execution_completed")
            return plan
        except Exception as exc:
            self._stage(plan, StageKind.EXECUTION, StageStatus.FAILED, str(exc))
            self.transition(execution_id, ExecutionStatus.FAILED, scope)
            plan.finished_at = utcnow()
            self.metrics.increment("tiktok_execution_failed")
            return plan
        finally:
            self.metrics.increment("tiktok_execution_running", -1)
            self.metrics.set(
                "tiktok_execution_latency_seconds", perf_counter() - started
            )
            self.infrastructure.cleanup(execution_id, scope)
            self.workers.pop(execution_id, None)
            self._stage(plan, StageKind.CLEANUP, StageStatus.COMPLETED)

    def pause(self, execution_id: str, scope: ExecutionScope) -> ExecutionPlan:
        plan = self.plans[execution_id]
        self._scoped(plan, scope)
        if plan.status not in {
            ExecutionStatus.QUEUED,
            ExecutionStatus.RUNNING,
        }:
            raise ValueError("Only queued or running executions may pause.")
        return self.transition(execution_id, ExecutionStatus.PAUSED, scope)

    def recover(self, execution_id: str, scope: ExecutionScope) -> ExecutionPlan:
        self._require(scope, "recover")
        plan = self.plans[execution_id]
        self._scoped(plan, scope)
        if plan.status not in {ExecutionStatus.PAUSED, ExecutionStatus.FAILED}:
            raise ValueError("Only paused or failed executions may recover.")
        checkpoints = [
            item for item in self.checkpoints.values() if item.execution_id == plan.id
        ]
        if not checkpoints:
            raise ValueError("Recovery requires an existing checkpoint.")
        self.transition(execution_id, ExecutionStatus.RECOVERING, scope)
        self.metrics.increment("tiktok_execution_recoveries")
        self._record(plan, scope, "execution.recovered", checkpoints[-1].id)
        recovered = self.transition(execution_id, ExecutionStatus.QUEUED, scope)
        self.queue.append(execution_id)
        return recovered

    def rollback(self, execution_id: str, scope: ExecutionScope) -> ExecutionPlan:
        self._require(scope, "rollback")
        plan = self.plans[execution_id]
        self._scoped(plan, scope)
        if plan.status not in {
            ExecutionStatus.FAILED,
            ExecutionStatus.RECOVERING,
        }:
            raise ValueError("Only failed or recovering executions may roll back.")
        pipeline = self._pipeline(execution_id)
        by_id = {step.id: step for step in pipeline.steps}
        for result in reversed(
            [item for item in self.results.values() if item.execution_id == plan.id]
        ):
            step = by_id[result.step_id]
            if result.success and step.rollback_action:
                self.infrastructure.rollback(step, result.output_reference, scope)
        self.infrastructure.cleanup(execution_id, scope)
        if execution_id in self.queue:
            self.queue.remove(execution_id)
        self.workers.pop(execution_id, None)
        self.transition(execution_id, ExecutionStatus.ROLLED_BACK, scope)
        self.metrics.increment("tiktok_execution_rollbacks")
        self._record(plan, scope, "rollback.audited")
        return plan

    def monitoring(self, scope: ExecutionScope) -> dict[str, Any]:
        self._require(scope, "read")
        plans = self.scoped_values(self.plans.values(), scope)
        stages = self.scoped_values(self.stages.values(), scope)
        return {
            "execution_health": "healthy"
            if not any(item.status is ExecutionStatus.FAILED for item in plans)
            else "degraded",
            "stage_progress": {item.kind.value: item.progress for item in stages},
            "resource_usage": {"active_workers": len(self.workers)},
            "runtime_status": {item.id: item.status.value for item in plans},
            "failure_detection": sum(
                item.status is ExecutionStatus.FAILED for item in plans
            ),
            "recovery_status": sum(
                item.status is ExecutionStatus.RECOVERING for item in plans
            ),
        }

    def analytics(self, scope: ExecutionScope) -> dict[str, float]:
        self._require(scope, "read")
        plans = self.scoped_values(self.plans.values(), scope)
        completed = sum(item.status is ExecutionStatus.COMPLETED for item in plans)
        failed = sum(item.status is ExecutionStatus.FAILED for item in plans)
        runtimes = [
            (item.finished_at - item.started_at).total_seconds()
            for item in plans
            if item.started_at and item.finished_at
        ]
        results = self.scoped_values(self.results.values(), scope)
        return {
            "execution_success": float(completed),
            "execution_failure": float(failed),
            "average_runtime": sum(runtimes) / len(runtimes) if runtimes else 0.0,
            "average_recovery": 0.0,
            "rollback_count": self.metrics.values["tiktok_execution_rollbacks"],
            "resource_consumption": float(len(results)),
        }

    def dashboard(self, scope: ExecutionScope) -> dict[str, Any]:
        plans = self.scoped_values(self.plans.values(), scope)
        return {
            "sections": [
                "Execution Overview",
                "Pipelines",
                "Stages",
                "Workers",
                "Checkpoints",
                "Rollback",
                "Results",
                "Monitoring",
                "Analytics",
            ],
            "execution_overview": {
                "total": len(plans),
                "running": sum(
                    item.status is ExecutionStatus.RUNNING for item in plans
                ),
                "queued": sum(item.status is ExecutionStatus.QUEUED for item in plans),
            },
            "pipelines": len(self.scoped_values(self.pipelines.values(), scope)),
            "stages": len(self.scoped_values(self.stages.values(), scope)),
            "workers": len(self.workers),
            "checkpoints": len(self.scoped_values(self.checkpoints.values(), scope)),
            "results": len(self.scoped_values(self.results.values(), scope)),
            "monitoring": self.monitoring(scope),
            "analytics": self.analytics(scope),
        }
