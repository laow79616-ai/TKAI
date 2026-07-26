"""Dependency-aware enterprise reasoning planner."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from ..models import ExecutionPlan, PlanTask


class Planner:
    def create(self, goal: str, subtasks: list[dict[str, Any]]) -> ExecutionPlan:
        tasks = tuple(
            PlanTask(
                id=str(item["id"]),
                goal=str(item.get("goal") or item["id"]),
                dependencies=tuple(
                    str(value) for value in item.get("dependencies", ())
                ),
                priority=int(item.get("priority", 50)),
            )
            for item in subtasks
        )
        if len({task.id for task in tasks}) != len(tasks):
            raise ValueError("Subtask IDs must be unique.")
        identifiers = {task.id for task in tasks}
        if any(set(task.dependencies) - identifiers for task in tasks):
            raise ValueError("Plan contains an unknown dependency.")
        order = self._order(tasks)
        return ExecutionPlan(goal=goal, subtasks=tasks, execution_order=order)

    @staticmethod
    def _order(tasks: tuple[PlanTask, ...]) -> tuple[str, ...]:
        incoming = {task.id: set(task.dependencies) for task in tasks}
        dependents: dict[str, set[str]] = defaultdict(set)
        priorities = {task.id: task.priority for task in tasks}
        for task in tasks:
            for dependency in task.dependencies:
                dependents[dependency].add(task.id)
        ready = [identifier for identifier, values in incoming.items() if not values]
        result: list[str] = []
        while ready:
            ready.sort(key=lambda item: (-priorities[item], item))
            current = ready.pop(0)
            result.append(current)
            for dependent in dependents[current]:
                incoming[dependent].discard(current)
                if not incoming[dependent]:
                    ready.append(dependent)
        if len(result) != len(tasks):
            raise ValueError("Plan contains a dependency loop.")
        return tuple(result)
