"""Tenant-scoped Enterprise AI Automation Platform domain service."""

from __future__ import annotations

import secrets
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass
from dataclasses import field as dataclass_field
from datetime import datetime, timedelta, timezone
from enum import Enum
from time import monotonic
from typing import Any

from .metrics import AutomationMetrics


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AutomationStatus(str, Enum):
    DRAFT = "draft"
    ENABLED = "enabled"
    DISABLED = "disabled"
    PAUSED = "paused"
    ARCHIVED = "archived"
    DELETED = "deleted"


class TriggerType(str, Enum):
    SCHEDULE = "schedule"
    WEBHOOK = "webhook"
    API = "api"
    EVENT = "event"
    WORKFLOW = "workflow"
    AGENT = "agent"
    KNOWLEDGE = "knowledge"
    APPLICATION = "application"
    MANUAL = "manual"


class ConditionType(str, Enum):
    BOOLEAN = "boolean"
    EXPRESSION = "expression"
    THRESHOLD = "threshold"
    STATE = "state"
    TIME = "time"
    DEPENDENCY = "dependency"
    CUSTOM = "custom"


class ActionType(str, Enum):
    WORKFLOW = "workflow"
    AGENT = "agent"
    APPLICATION = "application"
    NOTIFICATION = "notification"
    APPROVAL = "approval"
    SCRIPT_INTERFACE = "script_interface"
    CONNECTOR = "connector"
    MODEL = "model"
    KNOWLEDGE = "knowledge"


class PipelineMode(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    WAITING_APPROVAL = "waiting_approval"
    SKIPPED = "skipped"


@dataclass(frozen=True, slots=True)
class AutomationScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"automation:read"})

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Automation:
    id: str
    name: str
    description: str
    owner: str
    tenant: str
    workspace: str
    category: str
    status: AutomationStatus = AutomationStatus.DRAFT
    metadata: dict[str, Any] = dataclass_field(default_factory=dict)
    trigger_ids: tuple[str, ...] = ()
    pipeline_id: str | None = None
    policy_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        return value


@dataclass(slots=True)
class Trigger:
    id: str
    automation_id: str
    type: TriggerType
    tenant: str
    workspace: str
    config: dict[str, Any] = dataclass_field(default_factory=dict)
    enabled: bool = True
    secret_references: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Condition:
    id: str
    type: ConditionType
    field: str = ""
    operator: str = "equals"
    expected: Any = True
    config: dict[str, Any] = dataclass_field(default_factory=dict)

    def evaluate(self, context: Mapping[str, Any]) -> bool:
        if self.type is ConditionType.BOOLEAN:
            return bool(context.get(self.field, self.expected))
        if self.type is ConditionType.EXPRESSION:
            actual = context.get(self.field)
            comparisons = {
                "equals": actual == self.expected,
                "not_equals": actual != self.expected,
                "contains": self.expected in actual if actual is not None else False,
            }
            return bool(comparisons.get(self.operator, False))
        if self.type is ConditionType.THRESHOLD:
            actual = float(context.get(self.field, 0))
            expected = float(self.expected)
            return {
                "gt": actual > expected,
                "gte": actual >= expected,
                "lt": actual < expected,
                "lte": actual <= expected,
                "equals": actual == expected,
            }.get(self.operator, False)
        if self.type is ConditionType.STATE:
            return bool(context.get(self.field) == self.expected)
        if self.type is ConditionType.TIME:
            current = context.get(self.field, utcnow())
            return isinstance(current, datetime) and current >= self.expected
        if self.type is ConditionType.DEPENDENCY:
            return bool(context.get(self.field, False))
        evaluator = self.config.get("evaluator")
        return bool(evaluator(context)) if callable(evaluator) else False


@dataclass(slots=True)
class Action:
    id: str
    name: str
    type: ActionType
    tenant: str
    workspace: str
    config: dict[str, Any] = dataclass_field(default_factory=dict)
    condition_ids: tuple[str, ...] = ()
    secret_references: tuple[str, ...] = ()
    requires_approval: bool = False

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["type"] = self.type.value
        return value


@dataclass(slots=True)
class Pipeline:
    id: str
    name: str
    tenant: str
    workspace: str
    action_ids: tuple[str, ...]
    mode: PipelineMode = PipelineMode.SEQUENTIAL
    retry_limit: int = 0
    rollback_on_failure: bool = True
    checkpoint: bool = False
    timeout_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["mode"] = self.mode.value
        return value


@dataclass(slots=True)
class Schedule:
    id: str
    automation_id: str
    tenant: str
    workspace: str
    kind: str
    expression: str
    timezone: str = "UTC"
    retry_limit: int = 0
    missed_execution: str = "skip"
    next_run_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        if self.next_run_at:
            value["next_run_at"] = self.next_run_at.isoformat()
        return value


@dataclass(slots=True)
class RollbackPlan:
    id: str
    pipeline_id: str
    tenant: str
    workspace: str
    compensations: dict[str, str] = dataclass_field(default_factory=dict)
    restore_checkpoint: bool = True
    validation: str = "required"


@dataclass(slots=True)
class Approval:
    id: str
    automation_id: str
    tenant: str
    workspace: str
    requested_by: str
    status: str = "pending"
    decided_by: str | None = None
    decided_at: datetime | None = None


@dataclass(slots=True)
class Execution:
    id: str
    automation_id: str
    tenant: str
    workspace: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    attempts: int = 0
    failures: list[str] = dataclass_field(default_factory=list)
    checkpoints: list[dict[str, Any]] = dataclass_field(default_factory=list)
    results: dict[str, Any] = dataclass_field(default_factory=dict)
    approval_id: str | None = None
    started_at: datetime = dataclass_field(default_factory=utcnow)
    completed_at: datetime | None = None
    duration_seconds: float = 0

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["started_at"] = self.started_at.isoformat()
        if self.completed_at:
            value["completed_at"] = self.completed_at.isoformat()
        return value


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


ActionHandler = Callable[[Action, Mapping[str, Any]], Any]


class AutomationPlatform:
    """In-memory reference control plane with isolation, RBAC and audit."""

    TRANSITIONS = {
        AutomationStatus.DRAFT: {
            AutomationStatus.ENABLED,
            AutomationStatus.ARCHIVED,
            AutomationStatus.DELETED,
        },
        AutomationStatus.ENABLED: {
            AutomationStatus.DISABLED,
            AutomationStatus.PAUSED,
            AutomationStatus.ARCHIVED,
        },
        AutomationStatus.DISABLED: {
            AutomationStatus.ENABLED,
            AutomationStatus.ARCHIVED,
            AutomationStatus.DELETED,
        },
        AutomationStatus.PAUSED: {
            AutomationStatus.ENABLED,
            AutomationStatus.DISABLED,
            AutomationStatus.ARCHIVED,
        },
        AutomationStatus.ARCHIVED: {AutomationStatus.DELETED},
        AutomationStatus.DELETED: set(),
    }

    def __init__(self) -> None:
        self.automations: dict[str, Automation] = {}
        self.triggers: dict[str, Trigger] = {}
        self.conditions: dict[str, Condition] = {}
        self.actions: dict[str, Action] = {}
        self.pipelines: dict[str, Pipeline] = {}
        self.schedules: dict[str, Schedule] = {}
        self.rollback_plans: dict[str, RollbackPlan] = {}
        self.approvals: dict[str, Approval] = {}
        self.executions: list[Execution] = []
        self.audit: list[AuditEntry] = []
        self.metrics = AutomationMetrics()
        self._handlers: dict[ActionType, ActionHandler] = {}

    @staticmethod
    def _check(record: Any, scope: AutomationScope) -> None:
        if record.tenant != scope.tenant or record.workspace != scope.workspace:
            raise PermissionError("Cross-scope automation access denied.")

    @staticmethod
    def _require(scope: AutomationScope, permission: str) -> None:
        if (
            permission not in scope.permissions
            and "automation:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {permission}")

    def _audit(self, action: str, scope: AutomationScope, **metadata: Any) -> None:
        self.audit.append(
            AuditEntry(
                action, scope.actor, scope.tenant, scope.workspace, utcnow(), metadata
            )
        )

    def _scoped(self, values: Any, scope: AutomationScope) -> list[Any]:
        self._require(scope, "automation:read")
        return [
            value
            for value in values
            if value.tenant == scope.tenant and value.workspace == scope.workspace
        ]

    @staticmethod
    def _validate_secret_references(references: tuple[str, ...]) -> None:
        if any(
            not reference.startswith(("secret://", "vault://"))
            for reference in references
        ):
            raise ValueError("Secrets must use secret:// or vault:// references.")

    def create_automation(
        self, automation: Automation, scope: AutomationScope
    ) -> Automation:
        self._require(scope, "automation:write")
        self._check(automation, scope)
        if automation.id in self.automations:
            raise ValueError("Automation already exists.")
        self.automations[automation.id] = automation
        self.metrics.increment("automation_total")
        self._audit("automation.create", scope, automation_id=automation.id)
        return automation

    def list_automations(self, scope: AutomationScope) -> list[Automation]:
        return self._scoped(self.automations.values(), scope)

    def set_status(
        self, automation_id: str, status: AutomationStatus, scope: AutomationScope
    ) -> Automation:
        self._require(scope, "automation:write")
        automation = self.automations[automation_id]
        self._check(automation, scope)
        if status not in self.TRANSITIONS[automation.status]:
            current = automation.status.value
            raise ValueError(
                f"Invalid lifecycle transition: {current} -> {status.value}"
            )
        automation.status = status
        self._audit(
            "automation.status", scope, automation_id=automation_id, status=status.value
        )
        return automation

    def add_trigger(self, trigger: Trigger, scope: AutomationScope) -> Trigger:
        self._require(scope, "automation:write")
        self._check(trigger, scope)
        automation = self.automations[trigger.automation_id]
        self._check(automation, scope)
        self._validate_secret_references(trigger.secret_references)
        self.triggers[trigger.id] = trigger
        automation.trigger_ids = (*automation.trigger_ids, trigger.id)
        self._audit("trigger.create", scope, trigger_id=trigger.id)
        return trigger

    def add_condition(self, condition: Condition, scope: AutomationScope) -> Condition:
        self._require(scope, "automation:write")
        self.conditions[condition.id] = condition
        self._audit("condition.create", scope, condition_id=condition.id)
        return condition

    def add_action(self, action: Action, scope: AutomationScope) -> Action:
        self._require(scope, "automation:write")
        self._check(action, scope)
        self._validate_secret_references(action.secret_references)
        self.actions[action.id] = action
        self._audit("action.create", scope, action_id=action.id)
        return action

    def add_pipeline(self, pipeline: Pipeline, scope: AutomationScope) -> Pipeline:
        self._require(scope, "automation:write")
        self._check(pipeline, scope)
        if pipeline.retry_limit < 0 or (
            pipeline.timeout_seconds is not None and pipeline.timeout_seconds <= 0
        ):
            raise ValueError("Retry and timeout values must be valid.")
        for action_id in pipeline.action_ids:
            action = self.actions[action_id]
            self._check(action, scope)
        self.pipelines[pipeline.id] = pipeline
        self._audit("pipeline.create", scope, pipeline_id=pipeline.id)
        return pipeline

    def bind_pipeline(
        self, automation_id: str, pipeline_id: str, scope: AutomationScope
    ) -> Automation:
        self._require(scope, "automation:write")
        automation = self.automations[automation_id]
        pipeline = self.pipelines[pipeline_id]
        self._check(automation, scope)
        self._check(pipeline, scope)
        automation.pipeline_id = pipeline_id
        return automation

    def add_schedule(self, schedule: Schedule, scope: AutomationScope) -> Schedule:
        self._require(scope, "automation:write")
        self._check(schedule, scope)
        if schedule.kind not in {"cron", "interval", "calendar"}:
            raise ValueError("Unsupported schedule kind.")
        if schedule.missed_execution not in {"skip", "run_once", "catch_up"}:
            raise ValueError("Unsupported missed execution policy.")
        self.schedules[schedule.id] = schedule
        self._audit("schedule.create", scope, schedule_id=schedule.id)
        return schedule

    def due_schedules(
        self, scope: AutomationScope, at: datetime | None = None
    ) -> list[Schedule]:
        current = at or utcnow()
        return [
            schedule
            for schedule in self._scoped(self.schedules.values(), scope)
            if schedule.next_run_at is not None and schedule.next_run_at <= current
        ]

    def add_rollback_plan(
        self, plan: RollbackPlan, scope: AutomationScope
    ) -> RollbackPlan:
        self._require(scope, "automation:write")
        self._check(plan, scope)
        self.rollback_plans[plan.pipeline_id] = plan
        self._audit("rollback.plan.create", scope, plan_id=plan.id)
        return plan

    def request_approval(self, automation_id: str, scope: AutomationScope) -> Approval:
        self._require(scope, "automation:execute")
        automation = self.automations[automation_id]
        self._check(automation, scope)
        approval = Approval(
            secrets.token_hex(12),
            automation_id,
            scope.tenant,
            scope.workspace,
            scope.actor,
        )
        self.approvals[approval.id] = approval
        self._audit("approval.request", scope, approval_id=approval.id)
        return approval

    def decide_approval(
        self, approval_id: str, approved: bool, scope: AutomationScope
    ) -> Approval:
        self._require(scope, "automation:approve")
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

    def register_handler(self, action_type: ActionType, handler: ActionHandler) -> None:
        self._handlers[action_type] = handler

    def _conditions_pass(self, action: Action, context: Mapping[str, Any]) -> bool:
        return all(
            self.conditions[item].evaluate(context) for item in action.condition_ids
        )

    def run(
        self,
        automation_id: str,
        context: Mapping[str, Any],
        scope: AutomationScope,
        approval_id: str | None = None,
    ) -> Execution:
        self._require(scope, "automation:execute")
        automation = self.automations[automation_id]
        self._check(automation, scope)
        if automation.status is not AutomationStatus.ENABLED:
            raise ValueError("Only enabled automations can run.")
        if automation.pipeline_id is None:
            raise ValueError("Automation has no pipeline.")
        pipeline = self.pipelines[automation.pipeline_id]
        execution = Execution(
            secrets.token_hex(12), automation_id, scope.tenant, scope.workspace
        )
        self.executions.append(execution)
        self.metrics.increment("automation_runs_total")
        started = monotonic()
        execution.status = ExecutionStatus.RUNNING
        try:
            for action_id in pipeline.action_ids:
                action = self.actions[action_id]
                if not self._conditions_pass(action, context):
                    execution.results[action.id] = {"status": "skipped"}
                    continue
                if action.requires_approval:
                    approval = self.approvals.get(approval_id or "")
                    if (
                        approval is None
                        or approval.automation_id != automation_id
                        or approval.status != "approved"
                    ):
                        execution.status = ExecutionStatus.WAITING_APPROVAL
                        execution.approval_id = approval_id
                        return execution
                handler = self._handlers.get(
                    action.type, lambda item, payload: {"accepted": item.id}
                )
                last_error: Exception | None = None
                for attempt in range(pipeline.retry_limit + 1):
                    execution.attempts += 1
                    try:
                        if (
                            pipeline.timeout_seconds is not None
                            and monotonic() - started > pipeline.timeout_seconds
                        ):
                            raise TimeoutError("Pipeline timeout exceeded.")
                        execution.results[action.id] = handler(action, context)
                        last_error = None
                        break
                    except Exception as error:
                        last_error = error
                        execution.failures.append(str(error))
                        if attempt < pipeline.retry_limit:
                            self.metrics.increment("automation_retries_total")
                if last_error is not None:
                    raise last_error
                if pipeline.checkpoint:
                    execution.checkpoints.append(dict(execution.results))
            execution.status = ExecutionStatus.SUCCEEDED
        except Exception:
            self.metrics.increment("automation_failures_total")
            if pipeline.rollback_on_failure and pipeline.id in self.rollback_plans:
                plan = self.rollback_plans[pipeline.id]
                execution.results["rollback"] = {
                    "compensations": plan.compensations,
                    "checkpoint_restored": bool(
                        plan.restore_checkpoint and execution.checkpoints
                    ),
                    "validation": plan.validation,
                }
                execution.status = ExecutionStatus.ROLLED_BACK
            else:
                execution.status = ExecutionStatus.FAILED
        finally:
            execution.duration_seconds = monotonic() - started
            if execution.status is not ExecutionStatus.WAITING_APPROVAL:
                execution.completed_at = utcnow()
            self.metrics.increment(
                "automation_duration_seconds", execution.duration_seconds
            )
            self._audit(
                "automation.run",
                scope,
                automation_id=automation_id,
                execution_id=execution.id,
                status=execution.status.value,
            )
        return execution

    def run_due(
        self, scope: AutomationScope, at: datetime | None = None
    ) -> list[Execution]:
        executions = []
        for schedule in self.due_schedules(scope, at):
            automation = self.automations[schedule.automation_id]
            if automation.status is AutomationStatus.ENABLED:
                executions.append(self.run(automation.id, {"scheduled_at": at}, scope))
            schedule.next_run_at = (at or utcnow()) + timedelta(minutes=1)
        return executions

    def history(
        self, scope: AutomationScope, status: ExecutionStatus | None = None
    ) -> list[Execution]:
        values = self._scoped(self.executions, scope)
        return (
            values
            if status is None
            else [item for item in values if item.status is status]
        )

    def dashboard(self, scope: AutomationScope) -> dict[str, Any]:
        executions = self.history(scope)
        return {
            "automations": [item.to_dict() for item in self.list_automations(scope)],
            "triggers": [
                item.to_dict() for item in self._scoped(self.triggers.values(), scope)
            ],
            "pipelines": [
                item.to_dict() for item in self._scoped(self.pipelines.values(), scope)
            ],
            "executions": [item.to_dict() for item in executions],
            "history": [item.to_dict() for item in executions],
            "failures": [
                item.to_dict()
                for item in executions
                if item.status in {ExecutionStatus.FAILED, ExecutionStatus.ROLLED_BACK}
            ],
            "metrics": self.metrics.snapshot(),
        }


EnterpriseAIAutomationPlatform = AutomationPlatform

__all__ = (
    "Action",
    "ActionHandler",
    "ActionType",
    "Approval",
    "AuditEntry",
    "Automation",
    "AutomationPlatform",
    "AutomationScope",
    "AutomationStatus",
    "Condition",
    "ConditionType",
    "EnterpriseAIAutomationPlatform",
    "Execution",
    "ExecutionStatus",
    "Pipeline",
    "PipelineMode",
    "RollbackPlan",
    "Schedule",
    "Trigger",
    "TriggerType",
    "utcnow",
)
