"""Workflow task execution with retry semantics."""

from __future__ import annotations

from typing import Any

from tkai.core.exceptions import WorkflowError

from .events import Event, EventBus
from .task import Step


class Executor:
    """Execute individual steps and emit task lifecycle events."""

    def __init__(self, events: EventBus | None = None) -> None:
        self.events = events or EventBus()

    def execute(self, step: Step, context: dict[str, Any]) -> list[Any]:
        """Execute one step, honoring its condition, loop, and retry policy."""
        if not step.should_run(context):
            self.events.emit(Event("step.skipped", {"task": step.task.name}))
            return []

        results: list[Any] = []
        for _ in range(step.loop):
            results.append(self._run_with_retry(step, context))
        return results

    def _run_with_retry(self, step: Step, context: dict[str, Any]) -> Any:
        attempts = step.retries + 1
        for attempt in range(1, attempts + 1):
            self.events.emit(
                Event("task.started", {"task": step.task.name, "attempt": attempt})
            )
            try:
                result = step.task.run(context)
            except Exception as exc:
                self.events.emit(
                    Event(
                        "task.failed",
                        {"task": step.task.name, "attempt": attempt, "error": exc},
                    )
                )
                if attempt == attempts:
                    raise WorkflowError(
                        f"Task '{step.task.name}' failed after {attempts} attempt(s)"
                    ) from exc
            else:
                self.events.emit(
                    Event(
                        "task.completed",
                        {"task": step.task.name, "attempt": attempt, "result": result},
                    )
                )
                return result
        raise AssertionError("Retry loop must return or raise")
