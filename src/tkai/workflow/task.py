"""Tasks and steps used by the workflow engine."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

TaskHandler = Callable[[dict[str, Any]], Any]
Condition = Callable[[dict[str, Any]], bool]


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """Retry settings for an individual step."""

    max_attempts: int = 1
    delay: float = 0.0
    backoff: float = 1.0
    retry_on: tuple[type[Exception], ...] = (Exception,)


@dataclass(frozen=True, slots=True)
class StepDependency:
    """Named dependency required before a step may execute."""

    name: str


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
    name: str | None = None
    description: str = ""
    dependencies: tuple[str | StepDependency, ...] = ()
    timeout: float | None = None
    retry: RetryPolicy | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    continue_on_error: bool = False
    iterable: Any = None
    loop_condition: Condition | None = None
    max_iterations: int = 100

    def __post_init__(self) -> None:
        if self.name is None:
            self.name = self.task.name

    def should_run(self, context: dict[str, Any]) -> bool:
        """Return whether this step should run for the current context."""
        return self.enabled and (self.condition is None or self.condition(context))

    @property
    def dependency_names(self) -> tuple[str, ...]:
        """Return normalized dependency names."""
        return tuple(
            item.name if isinstance(item, StepDependency) else item
            for item in self.dependencies
        )
