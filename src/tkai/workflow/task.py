"""Tasks and steps used by the workflow engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

TaskHandler = Callable[[dict[str, Any]], Any]
Condition = Callable[[dict[str, Any]], bool]


@dataclass(slots=True)
class Task:
    """A named unit of work receiving the mutable workflow context."""

    name: str
    handler: TaskHandler

    def run(self, context: dict[str, Any]) -> Any:
        """Execute this task with the current workflow context."""
        return self.handler(context)


@dataclass(slots=True)
class Step:
    """Task execution policy supporting conditions, loops, and retries."""

    task: Task
    condition: Condition | None = None
    loop: int = 1
    retries: int = 0

    def should_run(self, context: dict[str, Any]) -> bool:
        """Return whether this step should run for the current context."""
        return self.condition is None or self.condition(context)
