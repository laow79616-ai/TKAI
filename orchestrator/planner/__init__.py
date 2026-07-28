"""Validated execution plan construction."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from ..models import (
    ExecutionPlan,
    ExecutionState,
    PlanStep,
    Priority,
    RouteType,
    Scope,
)


class Planner:
    def create(self, payload: dict[str, Any], scope: Scope) -> ExecutionPlan:
        steps = tuple(
            PlanStep(
                id=str(step["id"]),
                name=str(step.get("name", step["id"])),
                route=RouteType(str(step["route"])),
                target=str(step["target"]),
                dependencies=tuple(step.get("dependencies", ())),
                condition=step.get("condition"),
                metadata=dict(step.get("metadata", {})),
            )
            for step in payload.get("steps", ())
        )
        self._validate(steps)
        return ExecutionPlan(
            id=str(payload.get("id", uuid4())),
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            priority=Priority(int(payload.get("priority", Priority.NORMAL))),
            dependencies=tuple(payload.get("dependencies", ())),
            state=ExecutionState.PENDING,
            metadata=dict(payload.get("metadata", {})),
            scope=scope,
            steps=steps,
        )

    @staticmethod
    def _validate(steps: tuple[PlanStep, ...]) -> None:
        ids = {step.id for step in steps}
        if len(ids) != len(steps):
            raise ValueError("Step IDs must be unique.")
        for step in steps:
            if not set(step.dependencies) <= ids:
                raise ValueError("Step dependency does not exist.")
