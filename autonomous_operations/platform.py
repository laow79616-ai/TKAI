"""Enterprise AI Autonomous Operations control plane."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from time import monotonic
from typing import Any

from .metrics import AutonomousOperationsMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class OperationStatus(str, Enum):
    DRAFT = "draft"
    LEARNING = "learning"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    ROLLBACK = "rollback"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    DELETED = "deleted"


class OperationMode(str, Enum):
    SUPERVISED = "supervised"
    AUTONOMOUS = "autonomous"
    ADVISORY = "advisory"


class ObjectiveType(str, Enum):
    AVAILABILITY = "availability"
    LATENCY = "latency"
    COST = "cost"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"
    SECURITY = "security"
    COMPLIANCE = "compliance"
    CUSTOM = "custom"


class PolicyType(str, Enum):
    EXECUTION = "execution"
    SAFETY = "safety"
    APPROVAL = "approval"
    RETRY = "retry"
    ROLLBACK = "rollback"
    RESOURCE = "resource"
    CONSTRAINT = "constraint"


class StrategyType(str, Enum):
    REACTIVE = "reactive"
    PROACTIVE = "proactive"
    PREDICTIVE = "predictive"
    ADAPTIVE = "adaptive"
    SCHEDULED = "scheduled"
    EVENT_DRIVEN = "event_driven"
    HYBRID = "hybrid"


class ExecutionStatus(str, Enum):
    QUEUED = "queued"
    WAITING_APPROVAL = "waiting_approval"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, slots=True)
class OperationScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"autonomous_operations:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class AutonomousOperation:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    priority: int
    mode: OperationMode = OperationMode.SUPERVISED
    status: OperationStatus = OperationStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    objective_ids: tuple[str, ...] = ()
    policy_ids: tuple[str, ...] = ()
    strategy_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["mode"] = self.mode.value
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Objective:
    id: str
    operation_id: str
    tenant: str
    workspace: str
    type: ObjectiveType
    target: float
    weight: float = 1.0
    unit: str = ""
    custom_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Policy:
    id: str
    operation_id: str
    tenant: str
    workspace: str
    type: PolicyType
    rules: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Strategy:
    id: str
    operation_id: str
    tenant: str
    workspace: str
    type: StrategyType
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Task:
    id: str
    name: str
    dependencies: tuple[str, ...] = ()
    config: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False


@dataclass(slots=True)
class Approval:
    id: str
    operation_id: str
    tenant: str
    workspace: str
    requested_by: str
    status: str = "pending"
    decided_by: str | None = None
    decided_at: datetime | None = None


@dataclass(slots=True)
class Execution:
    id: str
    operation_id: str
    tenant: str
    workspace: str
    status: ExecutionStatus = ExecutionStatus.QUEUED
    results: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    checkpoints: list[dict[str, Any]] = field(default_factory=list)
    attempts: int = 0
    approval_id: str | None = None
    started_at: datetime = field(default_factory=utcnow)
    completed_at: datetime | None = None
    duration_seconds: float = 0

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            value["completed_at"] = self.completed_at.isoformat()
        return value


@dataclass(slots=True)
class Feedback:
    id: str
    operation_id: str
    tenant: str
    workspace: str
    metrics: dict[str, float] = field(default_factory=dict)
    telemetry: dict[str, Any] = field(default_factory=dict)
    health: str = "unknown"
    errors: tuple[str, ...] = ()
    human_feedback: str | None = None
    agent_feedback: str | None = None
    confidence: float = 0


@dataclass(slots=True)
class SafetyConfig:
    operation_id: str
    tenant: str
    workspace: str
    guardrails: dict[str, Any] = field(default_factory=dict)
    limits: dict[str, float] = field(default_factory=dict)
    kill_switch: bool = False
    approval_required: bool = False
    rollback_triggers: tuple[str, ...] = ()
    maximum_risk: float = 0.5


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    occurred_at: datetime
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["occurred_at"] = self.occurred_at.isoformat()
        return value


TaskHandler = Callable[[Task, Mapping[str, Any]], Any]


class AutonomousOperationsPlatform:
    """In-memory reference implementation with isolation, safety and audit."""

    TRANSITIONS = {
        OperationStatus.DRAFT: {
            OperationStatus.LEARNING,
            OperationStatus.READY,
            OperationStatus.ARCHIVED,
            OperationStatus.DELETED,
        },
        OperationStatus.LEARNING: {
            OperationStatus.READY,
            OperationStatus.PAUSED,
            OperationStatus.ARCHIVED,
        },
        OperationStatus.READY: {
            OperationStatus.RUNNING,
            OperationStatus.LEARNING,
            OperationStatus.ARCHIVED,
        },
        OperationStatus.RUNNING: {
            OperationStatus.PAUSED,
            OperationStatus.ROLLBACK,
            OperationStatus.COMPLETED,
        },
        OperationStatus.PAUSED: {
            OperationStatus.RUNNING,
            OperationStatus.ROLLBACK,
            OperationStatus.ARCHIVED,
        },
        OperationStatus.ROLLBACK: {
            OperationStatus.READY,
            OperationStatus.COMPLETED,
        },
        OperationStatus.COMPLETED: {
            OperationStatus.LEARNING,
            OperationStatus.ARCHIVED,
        },
        OperationStatus.ARCHIVED: {OperationStatus.DELETED},
        OperationStatus.DELETED: set(),
    }

    def __init__(self) -> None:
        self.operations: dict[str, AutonomousOperation] = {}
        self.objectives: dict[str, Objective] = {}
        self.policies: dict[str, Policy] = {}
        self.strategies: dict[str, Strategy] = {}
        self.tasks: dict[str, list[Task]] = {}
        self.approvals: dict[str, Approval] = {}
        self.executions: list[Execution] = []
        self.feedback: list[Feedback] = []
        self.safety: dict[str, SafetyConfig] = {}
        self.learning_versions: dict[str, int] = {}
        self.recommendations: dict[str, list[dict[str, Any]]] = {}
        self.audit: list[AuditEntry] = []
        self.metrics = AutonomousOperationsMetrics()
        self._handlers: dict[str, TaskHandler] = {}

    @staticmethod
    def _check(record: Any, scope: OperationScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope autonomous operation access denied.")

    @staticmethod
    def _require(scope: OperationScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "autonomous_operations:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: OperationScope, **metadata: Any) -> None:
        safe = {
            key: value for key, value in metadata.items() if "secret" not in key.lower()
        }
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), safe
            )
        )

    def _scoped(self, values: Any, scope: OperationScope) -> list[Any]:
        self._require(scope, "autonomous_operations:read")
        return [
            item
            for item in values
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def create_operation(
        self, operation: AutonomousOperation, scope: OperationScope
    ) -> AutonomousOperation:
        self._require(scope, "autonomous_operations:write")
        self._check(operation, scope)
        if operation.id in self.operations:
            raise ValueError("Autonomous operation already exists.")
        if operation.priority < 0:
            raise ValueError("Priority must be non-negative.")
        self.operations[operation.id] = operation
        self.metrics.increment("autonomous_operations_total")
        self._audit("autonomous_operation.create", scope, operation_id=operation.id)
        return operation

    def list_operations(self, scope: OperationScope) -> list[AutonomousOperation]:
        return self._scoped(self.operations.values(), scope)

    def set_status(
        self, operation_id: str, status: OperationStatus, scope: OperationScope
    ) -> AutonomousOperation:
        self._require(scope, "autonomous_operations:write")
        operation = self.operations[operation_id]
        self._check(operation, scope)
        if status not in self.TRANSITIONS[operation.status]:
            current = operation.status.value
            raise ValueError(
                f"Invalid lifecycle transition: {current} -> {status.value}"
            )
        operation.status = status
        self._audit(
            "autonomous_operation.status",
            scope,
            operation_id=operation_id,
            status=status.value,
        )
        return operation

    def add_objective(self, objective: Objective, scope: OperationScope) -> Objective:
        self._require(scope, "autonomous_operations:write")
        self._check(objective, scope)
        operation = self.operations[objective.operation_id]
        self._check(operation, scope)
        if not 0 < objective.weight <= 1:
            raise ValueError("Objective weight must be within (0, 1].")
        if objective.type is ObjectiveType.CUSTOM and not objective.custom_name:
            raise ValueError("Custom objectives require a name.")
        self.objectives[objective.id] = objective
        operation.objective_ids = (*operation.objective_ids, objective.id)
        self._audit("objective.create", scope, objective_id=objective.id)
        return objective

    def add_policy(self, policy: Policy, scope: OperationScope) -> Policy:
        self._require(scope, "autonomous_operations:write")
        self._check(policy, scope)
        operation = self.operations[policy.operation_id]
        self._check(operation, scope)
        forbidden = {"secret", "password", "token", "api_key"}
        if forbidden.intersection(key.lower() for key in policy.rules):
            raise ValueError("Policies may contain references, not secrets.")
        self.policies[policy.id] = policy
        operation.policy_ids = (*operation.policy_ids, policy.id)
        self._audit("policy.create", scope, policy_id=policy.id, version=policy.version)
        return policy

    def add_strategy(self, strategy: Strategy, scope: OperationScope) -> Strategy:
        self._require(scope, "autonomous_operations:write")
        self._check(strategy, scope)
        operation = self.operations[strategy.operation_id]
        self._check(operation, scope)
        self.strategies[strategy.id] = strategy
        operation.strategy_ids = (*operation.strategy_ids, strategy.id)
        self._audit("strategy.create", scope, strategy_id=strategy.id)
        return strategy

    def configure_tasks(
        self, operation_id: str, tasks: list[Task], scope: OperationScope
    ) -> list[Task]:
        self._require(scope, "autonomous_operations:write")
        operation = self.operations[operation_id]
        self._check(operation, scope)
        ids = {task.id for task in tasks}
        if len(ids) != len(tasks):
            raise ValueError("Task IDs must be unique.")
        if any(not set(task.dependencies).issubset(ids) for task in tasks):
            raise ValueError("Task dependency does not exist.")
        self._ordered(tasks)
        self.tasks[operation_id] = tasks
        self._audit("execution.tasks.configure", scope, operation_id=operation_id)
        return tasks

    @staticmethod
    def _ordered(tasks: list[Task]) -> list[Task]:
        pending = {task.id: task for task in tasks}
        completed: set[str] = set()
        ordered: list[Task] = []
        while pending:
            ready = [
                task
                for task in pending.values()
                if set(task.dependencies).issubset(completed)
            ]
            if not ready:
                raise ValueError("Cyclic task dependencies are not allowed.")
            for task in ready:
                ordered.append(task)
                completed.add(task.id)
                pending.pop(task.id)
        return ordered

    def configure_safety(
        self, config: SafetyConfig, scope: OperationScope
    ) -> SafetyConfig:
        self._require(scope, "autonomous_operations:write")
        self._check(config, scope)
        self._check(self.operations[config.operation_id], scope)
        if not 0 <= config.maximum_risk <= 1:
            raise ValueError("Maximum risk must be within [0, 1].")
        self.safety[config.operation_id] = config
        self._audit("safety.configure", scope, operation_id=config.operation_id)
        return config

    def set_kill_switch(
        self, operation_id: str, enabled: bool, scope: OperationScope
    ) -> SafetyConfig:
        self._require(scope, "autonomous_operations:admin")
        config = self.safety[operation_id]
        self._check(config, scope)
        config.kill_switch = enabled
        if enabled and self.operations[operation_id].status is OperationStatus.RUNNING:
            self.operations[operation_id].status = OperationStatus.PAUSED
        self._audit(
            "safety.kill_switch", scope, operation_id=operation_id, enabled=enabled
        )
        return config

    def assess_risk(
        self, operation_id: str, context: Mapping[str, Any], scope: OperationScope
    ) -> float:
        self._check(self.operations[operation_id], scope)
        risk = float(context.get("risk", 0))
        if not 0 <= risk <= 1:
            raise ValueError("Risk must be within [0, 1].")
        return risk

    def request_approval(self, operation_id: str, scope: OperationScope) -> Approval:
        self._require(scope, "autonomous_operations:execute")
        self._check(self.operations[operation_id], scope)
        approval = Approval(
            secrets.token_hex(12),
            operation_id,
            scope.tenant,
            scope.workspace,
            scope.actor,
        )
        self.approvals[approval.id] = approval
        self._audit("approval.request", scope, approval_id=approval.id)
        return approval

    def decide_approval(
        self, approval_id: str, approved: bool, scope: OperationScope
    ) -> Approval:
        self._require(scope, "autonomous_operations:approve")
        approval = self.approvals[approval_id]
        self._check(approval, scope)
        if approval.status != "pending":
            raise ValueError("Approval has already been decided.")
        approval.status = "approved" if approved else "rejected"
        approval.decided_by = scope.actor
        approval.decided_at = utcnow()
        self._audit(
            "approval.decide", scope, approval_id=approval.id, status=approval.status
        )
        return approval

    def register_handler(self, task_name: str, handler: TaskHandler) -> None:
        self._handlers[task_name] = handler

    def execute(
        self,
        operation_id: str,
        context: Mapping[str, Any],
        scope: OperationScope,
        approval_id: str | None = None,
    ) -> Execution:
        self._require(scope, "autonomous_operations:execute")
        operation = self.operations[operation_id]
        self._check(operation, scope)
        safety = self.safety.get(operation_id)
        if safety and safety.kill_switch:
            raise PermissionError("Operation blocked by kill switch.")
        if operation.status not in {OperationStatus.READY, OperationStatus.RUNNING}:
            raise ValueError("Only ready or running operations can execute.")
        risk = self.assess_risk(operation_id, context, scope)
        if safety and risk > safety.maximum_risk:
            raise PermissionError("Operation risk exceeds safety policy.")
        tasks = self._ordered(self.tasks.get(operation_id, []))
        needs_approval = (
            operation.mode is OperationMode.SUPERVISED
            or bool(safety and safety.approval_required)
            or any(task.requires_approval for task in tasks)
        )
        approval = self.approvals.get(approval_id or "")
        execution = Execution(
            secrets.token_hex(12), operation_id, scope.tenant, scope.workspace
        )
        self.executions.append(execution)
        self.metrics.increment("autonomous_executions_total")
        if needs_approval and (
            approval is None
            or approval.operation_id != operation_id
            or approval.status != "approved"
        ):
            execution.status = ExecutionStatus.WAITING_APPROVAL
            execution.approval_id = approval_id
            return execution
        retry_policy = next(
            (
                policy
                for policy in self.policies.values()
                if policy.operation_id == operation_id
                and policy.type is PolicyType.RETRY
                and policy.enabled
            ),
            None,
        )
        rollback_policy = any(
            policy.operation_id == operation_id
            and policy.type is PolicyType.ROLLBACK
            and policy.enabled
            for policy in self.policies.values()
        )
        retry_limit = int(retry_policy.rules.get("limit", 0)) if retry_policy else 0
        timeout = float(context.get("timeout_seconds", 0))
        started = monotonic()
        operation.status = OperationStatus.RUNNING
        execution.status = ExecutionStatus.RUNNING
        try:
            for task in tasks:
                error: Exception | None = None
                for _ in range(retry_limit + 1):
                    execution.attempts += 1
                    try:
                        if timeout and monotonic() - started > timeout:
                            raise TimeoutError("Autonomous execution timed out.")
                        handler = self._handlers.get(
                            task.name, lambda item, payload: {"accepted": item.id}
                        )
                        execution.results[task.id] = handler(task, context)
                        execution.checkpoints.append(dict(execution.results))
                        error = None
                        break
                    except Exception as caught:
                        error = caught
                        execution.errors.append(str(caught))
                if error:
                    raise error
            execution.status = ExecutionStatus.SUCCEEDED
            operation.status = OperationStatus.COMPLETED
            self.metrics.increment("autonomous_success_total")
        except TimeoutError:
            execution.status = ExecutionStatus.TIMED_OUT
            operation.status = OperationStatus.PAUSED
            self.metrics.increment("autonomous_failures_total")
        except Exception:
            self.metrics.increment("autonomous_failures_total")
            if rollback_policy:
                execution.status = ExecutionStatus.ROLLED_BACK
                execution.results["rollback"] = {
                    "checkpoint_restored": bool(execution.checkpoints)
                }
                operation.status = OperationStatus.ROLLBACK
                self.metrics.increment("autonomous_rollbacks_total")
            else:
                execution.status = ExecutionStatus.FAILED
                operation.status = OperationStatus.PAUSED
        finally:
            execution.duration_seconds = monotonic() - started
            execution.completed_at = utcnow()
            self.metrics.increment(
                "autonomous_latency_seconds", execution.duration_seconds
            )
            self._audit(
                "execution.complete",
                scope,
                operation_id=operation_id,
                execution_id=execution.id,
                status=execution.status.value,
            )
        return execution

    def record_feedback(self, item: Feedback, scope: OperationScope) -> Feedback:
        self._require(scope, "autonomous_operations:write")
        self._check(item, scope)
        self._check(self.operations[item.operation_id], scope)
        if not 0 <= item.confidence <= 1:
            raise ValueError("Feedback confidence must be within [0, 1].")
        self.feedback.append(item)
        self._audit("feedback.record", scope, feedback_id=item.id)
        return item

    def optimize(self, operation_id: str, scope: OperationScope) -> dict[str, Any]:
        self._require(scope, "autonomous_operations:write")
        self._check(self.operations[operation_id], scope)
        recent = [item for item in self.feedback if item.operation_id == operation_id]
        recommendation = {
            "resource_allocation": "rebalance" if recent else "maintain",
            "scheduling": "priority_weighted",
            "cost": "optimize",
            "latency": "minimize",
            "capacity": "autoscale",
            "energy_interface": "available",
        }
        self.recommendations.setdefault(operation_id, []).append(recommendation)
        self._audit("optimization.run", scope, operation_id=operation_id)
        return recommendation

    def adapt(
        self, operation_id: str, signals: Mapping[str, float], scope: OperationScope
    ) -> dict[str, Any]:
        self._require(scope, "autonomous_operations:write")
        self._check(self.operations[operation_id], scope)
        result = {
            "policy_adjustment": bool(signals),
            "threshold_adjustment": signals.get("confidence", 0) < 0.7,
            "dynamic_routing": signals.get("latency", 0) > 1,
            "scaling": signals.get("load", 0) > 0.8,
            "learning_signals": dict(signals),
        }
        self._audit("adaptation.run", scope, operation_id=operation_id)
        return result

    def learn(self, operation_id: str, scope: OperationScope) -> dict[str, Any]:
        self._require(scope, "autonomous_operations:write")
        operation = self.operations[operation_id]
        self._check(operation, scope)
        history = [
            item for item in self.executions if item.operation_id == operation_id
        ]
        successes = sum(item.status is ExecutionStatus.SUCCEEDED for item in history)
        version = self.learning_versions.get(operation_id, 0) + 1
        self.learning_versions[operation_id] = version
        result = {
            "historical_analysis": {"executions": len(history)},
            "outcome_evaluation": {
                "success_rate": successes / len(history) if history else 0
            },
            "recommendation_reference": self.recommendations.get(operation_id, [])[-1:]
            or None,
            "continuous_improvement": True,
            "version": version,
        }
        self.metrics.increment("autonomous_learning_cycles_total")
        self._audit("learning.cycle", scope, operation_id=operation_id, version=version)
        return result

    def dashboard(self, scope: OperationScope) -> dict[str, Any]:
        operations = self.list_operations(scope)
        ids = {item.id for item in operations}
        return {
            "operations": [item.to_dict() for item in operations],
            "objectives": [
                item.to_dict()
                for item in self.objectives.values()
                if item.operation_id in ids
            ],
            "policies": [
                item.to_dict()
                for item in self.policies.values()
                if item.operation_id in ids
            ],
            "strategies": [
                item.to_dict()
                for item in self.strategies.values()
                if item.operation_id in ids
            ],
            "executions": [
                item.to_dict() for item in self.executions if item.operation_id in ids
            ],
            "feedback": [
                asdict(item) for item in self.feedback if item.operation_id in ids
            ],
            "optimization": {
                item: values
                for item, values in self.recommendations.items()
                if item in ids
            },
            "learning": {
                item: version
                for item, version in self.learning_versions.items()
                if item in ids
            },
            "safety": [
                asdict(item)
                for item in self.safety.values()
                if item.operation_id in ids
            ],
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAIAutonomousOperationsPlatform = AutonomousOperationsPlatform

__all__ = (
    "Approval",
    "AuditEntry",
    "AutonomousOperation",
    "AutonomousOperationsPlatform",
    "EnterpriseAIAutonomousOperationsPlatform",
    "Execution",
    "ExecutionStatus",
    "Feedback",
    "Objective",
    "ObjectiveType",
    "OperationMode",
    "OperationScope",
    "OperationStatus",
    "Policy",
    "PolicyType",
    "SafetyConfig",
    "Strategy",
    "StrategyType",
    "Task",
    "TaskHandler",
    "utcnow",
)
