"""Fair, bounded, local scheduling across existing TikTok control-plane modules."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict, deque
from dataclasses import asdict
from datetime import timedelta
from time import perf_counter
from typing import Any
from uuid import uuid4

from .adapters import MODULES, TASK_MODULE, BoundedTestPort, SchedulerPort
from .metrics import SchedulerMetrics
from .models import (
    Allocation,
    Checkpoint,
    DependencyRequirement,
    Execution,
    Failure,
    FailureCategory,
    ScheduledTask,
    SchedulerLimits,
    SchedulerScope,
    TaskDependency,
    TaskStatus,
    TaskType,
    Worker,
    WorkerStatus,
    utcnow,
    validate_safe_payload,
)

TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.DRAFT: frozenset(
        {TaskStatus.PENDING_APPROVAL, TaskStatus.READY, TaskStatus.CANCELLED}
    ),
    TaskStatus.PENDING_APPROVAL: frozenset({TaskStatus.READY, TaskStatus.CANCELLED}),
    TaskStatus.READY: frozenset(
        {TaskStatus.QUEUED, TaskStatus.SCHEDULED, TaskStatus.CANCELLED}
    ),
    TaskStatus.SCHEDULED: frozenset(
        {TaskStatus.QUEUED, TaskStatus.PAUSED, TaskStatus.CANCELLED}
    ),
    TaskStatus.QUEUED: frozenset(
        {TaskStatus.ALLOCATED, TaskStatus.PAUSED, TaskStatus.CANCELLED}
    ),
    TaskStatus.ALLOCATED: frozenset(
        {
            TaskStatus.RUNNING,
            TaskStatus.QUEUED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.RUNNING: frozenset(
        {
            TaskStatus.PAUSED,
            TaskStatus.RETRYING,
            TaskStatus.RECOVERING,
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
            TaskStatus.CANCELLED,
        }
    ),
    TaskStatus.PAUSED: frozenset(
        {TaskStatus.READY, TaskStatus.QUEUED, TaskStatus.CANCELLED}
    ),
    TaskStatus.RETRYING: frozenset(
        {TaskStatus.QUEUED, TaskStatus.FAILED, TaskStatus.CANCELLED}
    ),
    TaskStatus.RECOVERING: frozenset(
        {TaskStatus.QUEUED, TaskStatus.FAILED, TaskStatus.CANCELLED}
    ),
    TaskStatus.COMPLETED: frozenset({TaskStatus.ARCHIVED}),
    TaskStatus.FAILED: frozenset(
        {TaskStatus.RETRYING, TaskStatus.RECOVERING, TaskStatus.ARCHIVED}
    ),
    TaskStatus.CANCELLED: frozenset({TaskStatus.ARCHIVED}),
    TaskStatus.ARCHIVED: frozenset({TaskStatus.DELETED}),
    TaskStatus.DELETED: frozenset(),
}


class TikTokAITaskScheduler:
    """Single-user local scheduler with tenant/workspace isolation and safety gates."""

    def __init__(
        self,
        ports: dict[str, SchedulerPort] | None = None,
        limits: SchedulerLimits | None = None,
    ) -> None:
        self.limits = limits or SchedulerLimits()
        self.limits.validate()
        fallback = BoundedTestPort()
        self.ports = {name: (ports or {}).get(name, fallback) for name in MODULES}
        self.tasks: dict[str, ScheduledTask] = {}
        self.dependencies: dict[str, list[TaskDependency]] = defaultdict(list)
        self.workers: dict[str, Worker] = {}
        self.allocations: dict[str, Allocation] = {}
        self.executions: dict[str, Execution] = {}
        self.checkpoints: dict[str, Checkpoint] = {}
        self.failures: dict[str, Failure] = {}
        self.queues: dict[str, deque[str]] = defaultdict(deque)
        self.delayed_until: dict[str, Any] = {}
        self.recovery_attempts: defaultdict[str, int] = defaultdict(int)
        self.audit: list[dict[str, Any]] = []
        self.metrics = SchedulerMetrics()
        self.kill_switch = False
        self.paused_workspaces: set[tuple[str, str]] = set()
        self.paused_accounts: set[str] = set()
        self.paused_features: set[TaskType] = set()
        self._rotation: deque[tuple[str, str]] = deque()

    @staticmethod
    def _require(scope: SchedulerScope, permission: str) -> None:
        required = f"tiktok:scheduler:{permission}"
        if (
            required not in scope.permissions
            and "tiktok:scheduler:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _scoped(item: Any, scope: SchedulerScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-tenant or cross-workspace access denied.")

    def _record(
        self, scope: SchedulerScope, action: str, resource: str, detail: str = ""
    ) -> None:
        lowered = detail.casefold()
        if any(
            marker in lowered
            for marker in ("password=", "secret=", "token=", "cookie=", "session=")
        ):
            raise ValueError("Secrets are forbidden in scheduler audit records.")
        self.audit.append(
            {
                "actor": scope.actor,
                "action": action,
                "resource": resource,
                "tenant": scope.tenant,
                "workspace": scope.workspace,
                "detail": detail,
                "timestamp": utcnow(),
            }
        )

    def scoped_values(self, values: Any, scope: SchedulerScope) -> list[Any]:
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def create_task(self, task: ScheduledTask, scope: SchedulerScope) -> ScheduledTask:
        self._require(scope, "write")
        self._scoped(task, scope)
        task.validate(self.limits)
        if task.id in self.tasks:
            raise ValueError("Task ID must be unique.")
        if len(self.tasks) >= self.limits.maximum_global_tasks:
            raise OverflowError("Global task admission limit reached.")
        workspace_count = sum(
            item.tenant == task.tenant and item.workspace == task.workspace
            for item in self.tasks.values()
        )
        if workspace_count >= self.limits.maximum_workspace_tasks:
            raise OverflowError("Workspace task admission limit reached.")
        self._check_resource_limit(
            task, "account_reference", self.limits.maximum_account_tasks
        )
        self._check_resource_limit(
            task, "browser_reference", self.limits.maximum_browser_tasks
        )
        self._check_resource_limit(
            task, "device_reference", self.limits.maximum_device_tasks
        )
        self._check_resource_limit(
            task, "proxy_reference", self.limits.maximum_proxy_tasks
        )
        self.tasks[task.id] = task
        self.metrics.increment("tiktok_scheduler_tasks_total")
        self._record(scope, "task.created", task.id, task.task_type.value)
        return task

    def _check_resource_limit(
        self, task: ScheduledTask, field: str, limit: int
    ) -> None:
        reference = getattr(task, field)
        if (
            reference
            and sum(
                getattr(item, field) == reference
                and item.status
                not in {
                    TaskStatus.COMPLETED,
                    TaskStatus.CANCELLED,
                    TaskStatus.ARCHIVED,
                    TaskStatus.DELETED,
                }
                for item in self.tasks.values()
            )
            >= limit
        ):
            raise OverflowError(f"{field} task admission limit reached.")

    def transition(
        self, task_id: str, status: TaskStatus, scope: SchedulerScope
    ) -> ScheduledTask:
        self._require(scope, "write")
        task = self.tasks[task_id]
        self._scoped(task, scope)
        if status not in TRANSITIONS[task.status]:
            raise ValueError(
                f"Invalid task transition: {task.status.value} -> {status.value}"
            )
        task.status = status
        task.version += 1
        task.updated_at = utcnow()
        self._record(scope, "task.transition", task_id, status.value)
        return task

    def approve(
        self, task_id: str, approval_reference: str, scope: SchedulerScope
    ) -> ScheduledTask:
        self._require(scope, "approve")
        if not approval_reference:
            raise ValueError("Approval reference is required.")
        task = self.tasks[task_id]
        self._scoped(task, scope)
        if task.status is not TaskStatus.PENDING_APPROVAL:
            raise ValueError("Only pending tasks can be approved.")
        task.approval_reference = approval_reference
        return self.transition(task_id, TaskStatus.READY, scope)

    def add_dependency(self, dependency: TaskDependency, scope: SchedulerScope) -> None:
        self._require(scope, "write")
        task, parent = self.tasks[dependency.task_id], self.tasks[dependency.depends_on]
        self._scoped(task, scope)
        self._scoped(parent, scope)
        if dependency.task_id == dependency.depends_on or self._reachable(
            dependency.depends_on, dependency.task_id
        ):
            raise ValueError("Task dependency cycle detected.")
        if (
            self._depth(dependency.depends_on) + 1
            > self.limits.maximum_dependency_depth
        ):
            raise ValueError("Maximum dependency depth exceeded.")
        if not 1 <= dependency.timeout_seconds <= self.limits.maximum_runtime_seconds:
            raise ValueError("Dependency timeout is outside configured bounds.")
        self.dependencies[dependency.task_id].append(dependency)
        self._record(
            scope, "dependency.created", dependency.task_id, dependency.depends_on
        )

    def _reachable(self, start: str, target: str) -> bool:
        pending, seen = [start], set()
        while pending:
            node = pending.pop()
            if node == target:
                return True
            if node not in seen:
                seen.add(node)
                pending.extend(
                    item.depends_on for item in self.dependencies.get(node, [])
                )
        return False

    def _depth(self, task_id: str, seen: set[str] | None = None) -> int:
        visited = set() if seen is None else seen
        if task_id in visited:
            raise ValueError("Task dependency cycle detected.")
        values = self.dependencies.get(task_id, [])
        if not values:
            return 0
        return 1 + max(
            self._depth(item.depends_on, visited | {task_id}) for item in values
        )

    def _dependencies_ready(self, task_id: str) -> bool:
        for dependency in self.dependencies.get(task_id, []):
            state = self.tasks[dependency.depends_on].status
            if (
                dependency.requirement is DependencyRequirement.SUCCESS
                and state is not TaskStatus.COMPLETED
            ):
                return False
            if (
                dependency.requirement is DependencyRequirement.COMPLETION
                and state
                not in {
                    TaskStatus.COMPLETED,
                    TaskStatus.FAILED,
                    TaskStatus.CANCELLED,
                }
            ):
                return False
        return True

    def enqueue(
        self, task_id: str, scope: SchedulerScope, queue: str = "global"
    ) -> ScheduledTask:
        self._require(scope, "execute")
        task = self.tasks[task_id]
        self._scoped(task, scope)
        if (
            self.kill_switch
            or (scope.tenant, scope.workspace) in self.paused_workspaces
        ):
            raise RuntimeError("Scheduler or workspace is paused.")
        if (
            task.account_reference in self.paused_accounts
            or task.task_type in self.paused_features
        ):
            raise RuntimeError("Account or task feature is paused.")
        if task.status not in {
            TaskStatus.READY,
            TaskStatus.SCHEDULED,
            TaskStatus.RETRYING,
            TaskStatus.RECOVERING,
        }:
            raise ValueError("Task is not eligible for queueing.")
        if (
            sum(len(value) for value in self.queues.values())
            >= self.limits.maximum_queue_depth
        ):
            raise OverflowError("Queue depth limit reached; backpressure active.")
        if not self._dependencies_ready(task_id):
            raise RuntimeError("Task dependencies are not satisfied.")
        if task.schedule.start_time and task.schedule.start_time > utcnow():
            self.delayed_until[task_id] = task.schedule.start_time
            queue = "delayed"
        self.transition(task_id, TaskStatus.QUEUED, scope)
        key = f"{scope.tenant}:{scope.workspace}:{queue}"
        self.queues[key].append(task_id)
        workspace_key = (scope.tenant, scope.workspace)
        if workspace_key not in self._rotation:
            self._rotation.append(workspace_key)
        self.metrics.increment("tiktok_scheduler_queued_total")
        self._update_queue_metric()
        return task

    def promote_due(self) -> int:
        promoted = 0
        now = utcnow()
        for task_id, due in list(self.delayed_until.items()):
            if due <= now:
                task = self.tasks[task_id]
                delayed = self.queues[f"{task.tenant}:{task.workspace}:delayed"]
                if task_id in delayed:
                    delayed.remove(task_id)
                self.queues[f"{task.tenant}:{task.workspace}:global"].append(task_id)
                del self.delayed_until[task_id]
                promoted += 1
        self._update_queue_metric()
        return promoted

    def register_worker(self, worker: Worker, scope: SchedulerScope) -> Worker:
        self._require(scope, "manage")
        if worker.id in self.workers or worker.capacity <= 0 or worker.capacity > 100:
            raise ValueError("Worker ID must be unique and capacity within [1, 100].")
        if worker.workspace_scope not in {"*", scope.workspace}:
            raise PermissionError("Worker workspace scope mismatch.")
        self.workers[worker.id] = worker
        self._record(scope, "worker.registered", worker.id, worker.worker_type)
        return worker

    def heartbeat_worker(
        self, worker_id: str, health: str, scope: SchedulerScope
    ) -> Worker:
        self._require(scope, "manage")
        worker = self.workers[worker_id]
        if worker.workspace_scope not in {"*", scope.workspace}:
            raise PermissionError("Worker workspace scope mismatch.")
        worker.heartbeat = worker.last_active = utcnow()
        worker.health = health
        worker.status = (
            WorkerStatus.UNHEALTHY
            if health != "healthy"
            else (WorkerStatus.ACTIVE if worker.current_load else WorkerStatus.IDLE)
        )
        return worker

    def _effective_priority(self, task: ScheduledTask) -> int:
        age_minutes = max(0, int((utcnow() - task.created_at).total_seconds() // 60))
        return min(100, int(task.priority) + min(40, age_minutes // 5))

    def dispatch_next(self, scope: SchedulerScope) -> Execution | None:
        self._require(scope, "execute")
        if self.kill_switch:
            return None
        active = sum(
            item.status is TaskStatus.RUNNING for item in self.executions.values()
        )
        if active >= self.limits.maximum_concurrent_executions:
            return None
        candidates: list[ScheduledTask] = []
        for key, queue in self.queues.items():
            if key.startswith(
                f"{scope.tenant}:{scope.workspace}:"
            ) and not key.endswith(":delayed"):
                candidates.extend(
                    self.tasks[item]
                    for item in queue
                    if self.tasks[item].status is TaskStatus.QUEUED
                )
        if not candidates:
            return None
        task = max(
            candidates,
            key=lambda item: (
                self._effective_priority(item),
                -item.created_at.timestamp(),
            ),
        )
        worker = next(
            (
                item
                for item in self.workers.values()
                if item.available
                and task.task_type in item.supported_task_types
                and item.workspace_scope in {"*", task.workspace}
            ),
            None,
        )
        if worker is None:
            return None
        for queue in self.queues.values():
            if task.id in queue:
                queue.remove(task.id)
                break
        allocation = Allocation(
            f"allocation-{uuid4().hex}",
            task.id,
            task.tenant,
            task.workspace,
            worker.id,
            self._resource_references(task),
            self.limits.reservation_expiry(),
        )
        self.allocations[allocation.id] = allocation
        worker.current_load += 1
        worker.status = WorkerStatus.ACTIVE
        self.transition(task.id, TaskStatus.ALLOCATED, scope)
        execution = Execution(
            f"execution-{uuid4().hex}", task.id, task.tenant, task.workspace, worker.id
        )
        self.executions[execution.id] = execution
        self._record(scope, "task.allocated", task.id, worker.id)
        self._update_queue_metric()
        self._update_worker_metric()
        return execution

    @staticmethod
    def _resource_references(task: ScheduledTask) -> dict[str, str]:
        return {
            key: value
            for key, value in {
                "account": task.account_reference,
                "browser": task.browser_reference,
                "device": task.device_reference,
                "proxy": task.proxy_reference,
                "workflow": task.workflow_reference,
            }.items()
            if value
        }

    def execute(self, execution_id: str, scope: SchedulerScope) -> Execution:
        self._require(scope, "execute")
        execution = self.executions[execution_id]
        self._scoped(execution, scope)
        task = self.tasks[execution.task_id]
        if self.kill_switch:
            raise RuntimeError("Scheduler kill switch is active.")
        if task.status is not TaskStatus.ALLOCATED:
            raise ValueError("Execution is not allocated.")
        if (
            task.task_type
            in {
                task.task_type.PUBLISHING_JOB,
                task.task_type.INTERACTION_TASK,
            }
            and not task.approval_reference
        ):
            return self.fail(
                execution_id, FailureCategory.APPROVAL, "Approval gate denied.", scope
            )
        if task.metadata.get("restriction_active") or task.metadata.get(
            "challenge_active"
        ):
            return self.fail(
                execution_id,
                FailureCategory.RISK,
                "Unresolved restriction or challenge.",
                scope,
            )
        port = self.ports[TASK_MODULE[task.task_type]]
        started = perf_counter()
        execution.started_at = utcnow()
        execution.status = TaskStatus.RUNNING
        self.transition(task.id, TaskStatus.RUNNING, scope)
        self.metrics.increment("tiktok_scheduler_running_total")
        try:
            port.preflight(task, scope)
            if execution.cancellation_requested:
                return self.cancel_execution(execution_id, scope)
            outcome = port.execute(task, scope)
            validate_safe_payload(outcome, self.limits.maximum_payload_size)
            execution.outcome = outcome
            execution.progress = 100
            execution.status = TaskStatus.COMPLETED
            execution.finished_at = utcnow()
            self.transition(task.id, TaskStatus.COMPLETED, scope)
            self.metrics.increment("tiktok_scheduler_completed_total")
            self._record(scope, "execution.completed", execution.id, task.id)
            self._release(execution)
            return execution
        except (RuntimeError, TimeoutError, ValueError) as exc:
            return self.fail(execution_id, FailureCategory.UNKNOWN, str(exc), scope)
        finally:
            elapsed = perf_counter() - started
            self.metrics.set("tiktok_scheduler_execution_seconds", elapsed)
            self.metrics.set("tiktok_scheduler_latency_seconds", elapsed)

    def create_checkpoint(
        self,
        execution_id: str,
        completed_steps: list[str],
        pending_steps: list[str],
        state: dict[str, Any],
        scope: SchedulerScope,
    ) -> Checkpoint:
        self._require(scope, "execute")
        execution = self.executions[execution_id]
        self._scoped(execution, scope)
        validate_safe_payload(state, self.limits.maximum_payload_size)
        payload = json.dumps(state, sort_keys=True, default=str)
        checkpoint = Checkpoint(
            f"checkpoint-{uuid4().hex}",
            execution_id,
            scope.tenant,
            scope.workspace,
            state,
            completed_steps,
            pending_steps,
            self._resource_references(self.tasks[execution.task_id]),
            execution.attempt,
            utcnow() + timedelta(seconds=self.limits.maximum_runtime_seconds),
            hashlib.sha256(payload.encode()).hexdigest(),
        )
        self.checkpoints[checkpoint.id] = checkpoint
        self._record(scope, "checkpoint.created", checkpoint.id, execution_id)
        return checkpoint

    def resume_checkpoint(self, checkpoint_id: str, scope: SchedulerScope) -> Execution:
        self._require(scope, "recover")
        checkpoint = self.checkpoints[checkpoint_id]
        self._scoped(checkpoint, scope)
        digest = hashlib.sha256(
            json.dumps(checkpoint.execution_state, sort_keys=True, default=str).encode()
        ).hexdigest()
        if checkpoint.expires_at <= utcnow() or digest != checkpoint.integrity:
            raise ValueError("Checkpoint is expired or failed integrity validation.")
        execution = self.executions[checkpoint.execution_id]
        task = self.tasks[execution.task_id]
        if task.metadata.get("restriction_active") or task.metadata.get(
            "challenge_active"
        ):
            raise RuntimeError(
                "Recovery stopped for an unresolved restriction or challenge."
            )
        if self.recovery_attempts[task.id] >= self.limits.maximum_recovery_attempts:
            raise RuntimeError("Maximum recovery attempts reached.")
        self.recovery_attempts[task.id] += 1
        if task.status is TaskStatus.FAILED:
            self.transition(task.id, TaskStatus.RECOVERING, scope)
        execution.attempt += 1
        self.metrics.increment("tiktok_scheduler_recovery_total")
        self.enqueue(task.id, scope, "recovery")
        return execution

    def fail(
        self,
        execution_id: str,
        category: FailureCategory,
        detail: str,
        scope: SchedulerScope,
    ) -> Execution:
        execution = self.executions[execution_id]
        self._scoped(execution, scope)
        task = self.tasks[execution.task_id]
        eligible = category in task.retry_policy.eligible_categories
        failure = Failure(
            f"failure-{uuid4().hex}",
            task.id,
            execution.id,
            task.tenant,
            task.workspace,
            category,
            detail[:500],
            eligible,
        )
        self.failures[failure.id] = failure
        execution.status = TaskStatus.FAILED
        execution.finished_at = utcnow()
        self.transition(task.id, TaskStatus.FAILED, scope)
        self.metrics.increment("tiktok_scheduler_failed_total")
        self._release(execution)
        if eligible and execution.attempt < task.retry_policy.maximum_attempts:
            self.transition(task.id, TaskStatus.RETRYING, scope)
            execution.attempt += 1
            self.delayed_until[task.id] = utcnow() + timedelta(
                seconds=task.retry_policy.delay_for(execution.attempt)
            )
            self.enqueue(task.id, scope, "retry")
            self.metrics.increment("tiktok_scheduler_retry_total")
        else:
            self.queues[f"{task.tenant}:{task.workspace}:dead_letter"].append(task.id)
            self.metrics.increment("tiktok_scheduler_dead_letter_total")
        self._record(scope, "execution.failed", execution.id, category.value)
        return execution

    def cancel_execution(self, execution_id: str, scope: SchedulerScope) -> Execution:
        self._require(scope, "execute")
        execution = self.executions[execution_id]
        self._scoped(execution, scope)
        task = self.tasks[execution.task_id]
        execution.cancellation_requested = True
        execution.status = TaskStatus.CANCELLED
        execution.finished_at = utcnow()
        if task.status in {TaskStatus.ALLOCATED, TaskStatus.RUNNING}:
            self.transition(task.id, TaskStatus.CANCELLED, scope)
        self._release(execution)
        self._record(scope, "execution.cancelled", execution.id)
        return execution

    def _release(self, execution: Execution) -> None:
        worker = self.workers.get(execution.worker_id)
        if worker:
            worker.current_load = max(0, worker.current_load - 1)
            worker.status = (
                WorkerStatus.ACTIVE if worker.current_load else WorkerStatus.IDLE
            )
        for allocation in self.allocations.values():
            if allocation.task_id == execution.task_id and not allocation.released:
                allocation.released = True
        self._update_worker_metric()

    def set_pause(
        self,
        scope: SchedulerScope,
        *,
        kill_switch: bool | None = None,
        workspace: bool | None = None,
        account_reference: str | None = None,
        feature: Any = None,
        paused: bool = True,
    ) -> None:
        self._require(scope, "manage")
        if kill_switch is not None:
            self.kill_switch = kill_switch
        if workspace is not None:
            key = (scope.tenant, scope.workspace)
            (
                self.paused_workspaces.add
                if workspace
                else self.paused_workspaces.discard
            )(key)
        if account_reference:
            (self.paused_accounts.add if paused else self.paused_accounts.discard)(
                account_reference
            )
        if feature is not None:
            (self.paused_features.add if paused else self.paused_features.discard)(
                feature
            )
        self._record(scope, "safety.pause.updated", scope.workspace)

    def _update_queue_metric(self) -> None:
        self.metrics.set(
            "tiktok_scheduler_queue_depth",
            sum(len(value) for value in self.queues.values()),
        )

    def _update_worker_metric(self) -> None:
        capacity = sum(worker.capacity for worker in self.workers.values())
        load = sum(worker.current_load for worker in self.workers.values())
        self.metrics.set(
            "tiktok_scheduler_worker_utilization", load / capacity if capacity else 0
        )

    def telemetry(self, scope: SchedulerScope) -> dict[str, Any]:
        self._require(scope, "read")
        tasks = self.scoped_values(self.tasks.values(), scope)
        return {
            "queue_depth": sum(
                len(queue)
                for key, queue in self.queues.items()
                if key.startswith(f"{scope.tenant}:{scope.workspace}:")
            ),
            "queued_tasks": sum(item.status is TaskStatus.QUEUED for item in tasks),
            "running_tasks": sum(item.status is TaskStatus.RUNNING for item in tasks),
            "completed_tasks": sum(
                item.status is TaskStatus.COMPLETED for item in tasks
            ),
            "failed_tasks": sum(item.status is TaskStatus.FAILED for item in tasks),
            "retrying_tasks": sum(item.status is TaskStatus.RETRYING for item in tasks),
            "recovery_tasks": sum(
                item.status is TaskStatus.RECOVERING for item in tasks
            ),
            "dead_letter_tasks": len(
                self.queues[f"{scope.tenant}:{scope.workspace}:dead_letter"]
            ),
            "worker_utilization": self.metrics.values[
                "tiktok_scheduler_worker_utilization"
            ],
        }

    def statistics(self, scope: SchedulerScope) -> dict[str, Any]:
        tasks = self.scoped_values(self.tasks.values(), scope)
        volume = len(tasks)
        completed = sum(item.status is TaskStatus.COMPLETED for item in tasks)
        failed = sum(item.status is TaskStatus.FAILED for item in tasks)
        distribution: defaultdict[str, int] = defaultdict(int)
        for task in tasks:
            distribution[task.task_type.value] += 1
        return {
            "task_volume": volume,
            "success_rate": completed / volume if volume else 0,
            "failure_rate": failed / volume if volume else 0,
            "retry_rate": self.metrics.values["tiktok_scheduler_retry_total"] / volume
            if volume
            else 0,
            "recovery_success": self.metrics.values["tiktok_scheduler_recovery_total"],
            "average_queue_time": self.metrics.values[
                "tiktok_scheduler_queue_wait_seconds"
            ],
            "average_execution_time": self.metrics.values[
                "tiktok_scheduler_execution_seconds"
            ],
            "peak_concurrency": self.limits.maximum_concurrent_executions,
            "resource_utilization": self.metrics.values[
                "tiktok_scheduler_worker_utilization"
            ],
            "task_type_distribution": dict(distribution),
        }

    def dashboard(self, scope: SchedulerScope) -> dict[str, Any]:
        return {
            "title": "TikTok AI Task Scheduler",
            "sections": [
                "Scheduler Overview",
                "Tasks",
                "Queues",
                "Schedules",
                "Dependencies",
                "Allocations",
                "Workers",
                "Executions",
                "Checkpoints",
                "Retries",
                "Failures",
                "Recovery",
                "Limits",
                "Telemetry",
                "Statistics",
            ],
            "safety": {
                "kill_switch": self.kill_switch,
                "workspace_paused": (scope.tenant, scope.workspace)
                in self.paused_workspaces,
                "captcha_bypass": False,
                "restriction_circumvention": False,
                "security_bypass": False,
            },
            "telemetry": self.telemetry(scope),
            "statistics": self.statistics(scope),
            "limits": asdict(self.limits),
        }
