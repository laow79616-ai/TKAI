"""Reference-only V7 Unified Workflow Orchestration Framework."""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import replace
from threading import RLock
from uuid import uuid4

from tkai.v7.security import AccessController, Principal, filter_secrets

from .contracts import (
    HistoryEntry,
    RecoveryPlan,
    ValidationIssue,
    ValidationReport,
    Workflow,
    WorkflowLifecycle,
    WorkflowPlan,
    serialize,
    utc_now,
)

LIFECYCLE_TRANSITIONS: Mapping[WorkflowLifecycle, frozenset[WorkflowLifecycle]] = {
    WorkflowLifecycle.DRAFT: frozenset(
        {WorkflowLifecycle.VALIDATED, WorkflowLifecycle.CANCELLED}
    ),
    WorkflowLifecycle.VALIDATED: frozenset(
        {WorkflowLifecycle.READY, WorkflowLifecycle.DRAFT, WorkflowLifecycle.CANCELLED}
    ),
    WorkflowLifecycle.READY: frozenset(
        {
            WorkflowLifecycle.PLANNED,
            WorkflowLifecycle.PAUSED,
            WorkflowLifecycle.CANCELLED,
        }
    ),
    WorkflowLifecycle.PLANNED: frozenset(
        {
            WorkflowLifecycle.QUEUED,
            WorkflowLifecycle.PAUSED,
            WorkflowLifecycle.CANCELLED,
        }
    ),
    WorkflowLifecycle.QUEUED: frozenset(
        {WorkflowLifecycle.PAUSED, WorkflowLifecycle.CANCELLED}
    ),
    WorkflowLifecycle.PAUSED: frozenset(
        {
            WorkflowLifecycle.READY,
            WorkflowLifecycle.PLANNED,
            WorkflowLifecycle.CANCELLED,
        }
    ),
    WorkflowLifecycle.CANCELLED: frozenset({WorkflowLifecycle.ARCHIVED}),
    WorkflowLifecycle.ARCHIVED: frozenset({WorkflowLifecycle.DELETED}),
    WorkflowLifecycle.DELETED: frozenset(),
}

METRIC_NAMES = (
    "v7_workflow_registered_total",
    "v7_workflow_validations_total",
    "v7_workflow_validation_failures_total",
    "v7_workflow_plans_total",
    "v7_workflow_plan_failures_total",
    "v7_workflow_transitions_total",
    "v7_workflow_recoveries_total",
)


class WorkflowFrameworkError(RuntimeError):
    pass


class WorkflowValidationError(WorkflowFrameworkError):
    pass


class DependencyCycleError(WorkflowValidationError):
    pass


class IllegalLifecycleTransition(WorkflowFrameworkError):
    pass


class WorkflowRegistry:
    def __init__(self) -> None:
        self._workflows: dict[str, Workflow] = {}
        self._lock = RLock()

    def register(self, workflow: Workflow) -> Workflow:
        with self._lock:
            if workflow.workflow_id in self._workflows:
                raise WorkflowValidationError(
                    f"workflow already registered: {workflow.workflow_id}"
                )
            self._workflows[workflow.workflow_id] = workflow
            return workflow

    def get(self, workflow_id: str) -> Workflow:
        try:
            return self._workflows[workflow_id]
        except KeyError as error:
            raise KeyError(f"unknown workflow: {workflow_id}") from error

    def replace(self, workflow: Workflow) -> Workflow:
        with self._lock:
            if workflow.workflow_id not in self._workflows:
                raise KeyError(f"unknown workflow: {workflow.workflow_id}")
            self._workflows[workflow.workflow_id] = workflow
            return workflow

    def list(self) -> tuple[Workflow, ...]:
        return tuple(self._workflows[key] for key in sorted(self._workflows))


class WorkflowSecurity:
    def __init__(self, access: AccessController | None = None) -> None:
        self.access = access

    def authorize(
        self,
        workflow: Workflow,
        capability: str,
        *,
        principal: Principal | None = None,
        tenant_reference: str | None = None,
        workspace_reference: str | None = None,
        owner: str | None = None,
    ) -> None:
        if self.access is not None:
            if principal is None:
                raise PermissionError("principal required")
            self.access.require(principal, capability)
        if tenant_reference and workflow.scope.tenant_reference != tenant_reference:
            raise PermissionError("tenant isolation violation")
        if workspace_reference and (
            workflow.scope.workspace_reference != workspace_reference
        ):
            raise PermissionError("workspace isolation violation")
        if owner and workflow.owner != owner:
            raise PermissionError("workflow isolation violation")


class Metrics:
    def __init__(self) -> None:
        self._values = {name: 0.0 for name in METRIC_NAMES}

    def increment(self, name: str) -> None:
        self._values[name] += 1

    def snapshot(self) -> dict[str, float]:
        return dict(self._values)


class TracingHooks:
    def __init__(self) -> None:
        self._hooks: list[Callable[[str, Mapping[str, object]], None]] = []

    def register(self, hook: Callable[[str, Mapping[str, object]], None]) -> None:
        self._hooks.append(hook)

    def emit(self, name: str, attributes: Mapping[str, object]) -> None:
        safe = filter_secrets(attributes)
        for hook in self._hooks:
            hook(name, safe)


class WorkflowFramework:
    """Coordinates metadata and plans; it deliberately has no execution method."""

    def __init__(
        self,
        registry: WorkflowRegistry | None = None,
        *,
        security: WorkflowSecurity | None = None,
        max_plan_size: int = 1000,
    ) -> None:
        if max_plan_size < 1:
            raise ValueError("max_plan_size must be positive")
        self.registry = registry or WorkflowRegistry()
        self.security = security or WorkflowSecurity()
        self.max_plan_size = max_plan_size
        self.metrics = Metrics()
        self.tracing = TracingHooks()
        self.plans: list[WorkflowPlan] = []
        self.recoveries: list[RecoveryPlan] = []
        self.history: list[HistoryEntry] = []
        self.logs: list[dict[str, object]] = []

    def _record(
        self,
        workflow_id: str,
        category: str,
        action: str,
        actor: str,
        reference: str | None = None,
        details: Mapping[str, object] | None = None,
    ) -> None:
        entry = HistoryEntry(
            str(uuid4()), workflow_id, category, action, actor, reference, details or {}
        )
        self.history.append(entry)
        self.logs.append(
            {
                "timestamp": entry.timestamp,
                "level": "info",
                "event": f"workflow.{action}",
                "workflow_id": workflow_id,
                "actor": actor,
                "details": filter_secrets(details or {}),
            }
        )

    def register(self, workflow: Workflow, *, actor: str = "system") -> Workflow:
        result = self.registry.register(workflow)
        self.metrics.increment("v7_workflow_registered_total")
        self._record(workflow.workflow_id, "workflow", "registered", actor)
        self.tracing.emit("workflow.registered", {"workflow_id": workflow.workflow_id})
        return result

    def validate(self, workflow_id: str, *, actor: str = "system") -> ValidationReport:
        workflow = self.registry.get(workflow_id)
        issues: list[ValidationIssue] = []
        if not workflow.definition:
            issues.append(
                ValidationIssue(
                    "definition_empty", "definition is required", workflow_id
                )
            )
        if not re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", workflow.version):
            issues.append(
                ValidationIssue(
                    "version_invalid", "version must be semantic", workflow_id
                )
            )
        if "://" not in workflow.state_reference:
            issues.append(
                ValidationIssue(
                    "state_reference_invalid",
                    "state reference must be reference-only",
                    workflow_id,
                )
            )
        known = {item.workflow_id: item for item in self.registry.list()}
        for dependency in workflow.dependencies:
            target = known.get(dependency.workflow_id)
            if target is None and not dependency.optional:
                issues.append(
                    ValidationIssue(
                        "dependency_missing",
                        f"dependency is not registered: {dependency.workflow_id}",
                        workflow_id,
                    )
                )
            elif (
                target
                and dependency.required_version
                and target.version != dependency.required_version
            ):
                issues.append(
                    ValidationIssue(
                        "dependency_version_mismatch",
                        f"dependency version mismatch: {dependency.workflow_id}",
                        workflow_id,
                    )
                )
            if target and target.scope != workflow.scope:
                issues.append(
                    ValidationIssue(
                        "dependency_isolation_violation",
                        f"dependency crosses workflow scope: {dependency.workflow_id}",
                        workflow_id,
                    )
                )
        for constraint in workflow.constraints:
            if not constraint.satisfied:
                issues.append(
                    ValidationIssue(
                        "constraint_unsatisfied", constraint.name, workflow_id
                    )
                )
        schedule = workflow.schedule
        if not 0 <= schedule.priority <= 100:
            issues.append(
                ValidationIssue(
                    "schedule_priority_invalid",
                    "priority must be between 0 and 100",
                    workflow_id,
                )
            )
        if (
            schedule.window_start
            and schedule.window_end
            and schedule.window_start > schedule.window_end
        ):
            issues.append(
                ValidationIssue(
                    "schedule_window_invalid",
                    "planning window start follows end",
                    workflow_id,
                )
            )
        report = ValidationReport(workflow_id, not issues, tuple(issues))
        self.metrics.increment("v7_workflow_validations_total")
        if issues:
            self.metrics.increment("v7_workflow_validation_failures_total")
        self._record(
            workflow_id,
            "validation",
            "validated",
            actor,
            details={"valid": report.valid, "issues": len(issues)},
        )
        return report

    def _ordered_dependencies(self, workflow_id: str) -> tuple[str, ...]:
        ordered: list[str] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(item_id: str) -> None:
            if item_id in visiting:
                raise DependencyCycleError(f"dependency cycle at {item_id}")
            if item_id in visited:
                return
            visiting.add(item_id)
            item = self.registry.get(item_id)
            for dependency in sorted(
                item.dependencies, key=lambda value: value.workflow_id
            ):
                try:
                    self.registry.get(dependency.workflow_id)
                except KeyError:
                    if dependency.optional:
                        continue
                    raise
                visit(dependency.workflow_id)
            visiting.remove(item_id)
            visited.add(item_id)
            ordered.append(item_id)

        visit(workflow_id)
        return tuple(ordered)

    def plan(self, workflow_id: str, *, actor: str = "system") -> WorkflowPlan:
        workflow = self.registry.get(workflow_id)
        report = self.validate(workflow_id, actor=actor)
        issues = [issue.message for issue in report.issues]
        try:
            ordered = self._ordered_dependencies(workflow_id)
        except (DependencyCycleError, KeyError) as error:
            ordered = ()
            issues.append(str(error))
        bounded = len(ordered) <= self.max_plan_size
        if not bounded:
            issues.append("plan exceeds orchestration bound")
        plan = WorkflowPlan(
            str(uuid4()),
            workflow_id,
            ordered,
            ready=not issues,
            bounded=bounded,
            issues=tuple(issues),
            schedule=workflow.schedule,
        )
        self.plans.append(plan)
        self.metrics.increment("v7_workflow_plans_total")
        if issues:
            self.metrics.increment("v7_workflow_plan_failures_total")
        self._record(
            workflow_id,
            "planning",
            "planned",
            actor,
            plan.plan_id,
            {"ready": plan.ready, "reference_only": True},
        )
        self.tracing.emit(
            "workflow.planned",
            {"workflow_id": workflow_id, "plan_id": plan.plan_id},
        )
        return plan

    orchestrate = plan

    def transition(
        self,
        workflow_id: str,
        lifecycle: WorkflowLifecycle,
        *,
        actor: str = "system",
        principal: Principal | None = None,
        tenant_reference: str | None = None,
        workspace_reference: str | None = None,
    ) -> Workflow:
        workflow = self.registry.get(workflow_id)
        self.security.authorize(
            workflow,
            "workflow.transition",
            principal=principal,
            tenant_reference=tenant_reference,
            workspace_reference=workspace_reference,
        )
        if lifecycle not in LIFECYCLE_TRANSITIONS[workflow.lifecycle]:
            raise IllegalLifecycleTransition(
                f"illegal transition: {workflow.lifecycle.value} -> {lifecycle.value}"
            )
        updated = replace(workflow, lifecycle=lifecycle, updated_at=utc_now())
        self.registry.replace(updated)
        self.metrics.increment("v7_workflow_transitions_total")
        self._record(workflow_id, "lifecycle", lifecycle.value, actor)
        return updated

    def plan_recovery(
        self,
        workflow_id: str,
        target_reference: str,
        *,
        rollback: bool = False,
        actor: str = "system",
    ) -> RecoveryPlan:
        workflow = self.registry.get(workflow_id)
        issues = []
        if "://" not in target_reference:
            issues.append("recovery target must be a reference")
        if workflow.lifecycle is WorkflowLifecycle.DELETED:
            issues.append("deleted workflows cannot be recovered")
        plan = RecoveryPlan(
            str(uuid4()),
            workflow_id,
            "rollback" if rollback else "recovery",
            target_reference,
            not issues,
            rollback=rollback,
            issues=tuple(issues),
        )
        self.recoveries.append(plan)
        self.metrics.increment("v7_workflow_recoveries_total")
        self._record(
            workflow_id,
            "recovery",
            "planned",
            actor,
            plan.recovery_id,
            {"ready": plan.ready, "rollback": rollback},
        )
        return plan

    def snapshot(self) -> dict[str, object]:
        workflows = self.registry.list()
        history = tuple(self.history)
        return {
            "registry": serialize(workflows),
            "definitions": serialize(
                tuple(
                    {
                        "workflow_id": item.workflow_id,
                        "version": item.version,
                        "definition": item.definition,
                    }
                    for item in workflows
                )
            ),
            "planner": serialize(tuple(self.plans)),
            "dependencies": serialize(
                tuple(
                    {
                        "workflow_id": item.workflow_id,
                        "dependencies": item.dependencies,
                    }
                    for item in workflows
                )
            ),
            "constraints": serialize(
                tuple(
                    {"workflow_id": item.workflow_id, "constraints": item.constraints}
                    for item in workflows
                )
            ),
            "lifecycle": serialize(
                tuple(
                    {"workflow_id": item.workflow_id, "lifecycle": item.lifecycle}
                    for item in workflows
                )
            ),
            "history": serialize(history),
            "recovery": serialize(tuple(self.recoveries)),
            "metrics": self.metrics.snapshot(),
            "audit": serialize(history),
            "health": {
                "status": "healthy",
                "workflows": len(workflows),
                "ready_plans": sum(plan.ready for plan in self.plans),
                "execution_enabled": False,
            },
        }


GLOBAL_WORKFLOW_FRAMEWORK = WorkflowFramework()

__all__ = (
    "DependencyCycleError",
    "GLOBAL_WORKFLOW_FRAMEWORK",
    "IllegalLifecycleTransition",
    "LIFECYCLE_TRANSITIONS",
    "METRIC_NAMES",
    "Metrics",
    "TracingHooks",
    "WorkflowFramework",
    "WorkflowFrameworkError",
    "WorkflowRegistry",
    "WorkflowSecurity",
    "WorkflowValidationError",
)
