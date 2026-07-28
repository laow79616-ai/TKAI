"""Constraint, consistency, loop, conflict, and safety validation."""

from __future__ import annotations

from collections import Counter
from typing import Any

from ..models import ExecutionPlan, ValidationResult


class ReasoningValidator:
    def validate(
        self,
        plan: ExecutionPlan,
        constraints: dict[str, Any] | None = None,
    ) -> ValidationResult:
        active = constraints or {}
        failures: list[str] = []
        identifiers = [task.id for task in plan.subtasks]
        if len(identifiers) != len(set(identifiers)):
            failures.append("consistency: duplicate task identifiers")
        if len(plan.execution_order) != len(plan.subtasks):
            failures.append("loop: execution plan is cyclic")
        denied = set(str(item) for item in active.get("denied_tasks", ()))
        if denied.intersection(identifiers):
            failures.append("constraint: plan contains denied tasks")
        conflicts = Counter(
            str(item) for task in plan.subtasks for item in task.dependencies
        )
        if any(task.id in task.dependencies for task in plan.subtasks):
            failures.append("conflict: task depends on itself")
        if active.get("safe") is False:
            failures.append("safety: policy rejected the plan")
        warnings = (
            ("high dependency fan-in",)
            if any(value > 10 for value in conflicts.values())
            else ()
        )
        return ValidationResult(not failures, tuple(failures), warnings)
