"""Single-owner workflow runtime state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .control import ExecutionState
from .dispatch import Dispatcher
from .models import WorkflowContext
from .task import Step


@dataclass(slots=True)
class ExecutionContext:
    workflow: WorkflowContext = field(default_factory=WorkflowContext)
    state: ExecutionState = ExecutionState.PENDING
    completed: set[str] = field(default_factory=set)

    def pause(self) -> None:
        self.state = ExecutionState.PAUSED

    def resume(self) -> None:
        self.state = ExecutionState.RUNNING

    def cancel(self) -> None:
        self.state = ExecutionState.CANCELLED

    def can_dispatch(self) -> bool:
        return self.state is ExecutionState.RUNNING


class WorkflowRuntime:
    def __init__(
        self, steps: list[Step], context: dict[str, Any] | None = None
    ) -> None:
        self.context = ExecutionContext(WorkflowContext(inputs=context or {}))
        self.dispatcher = Dispatcher(steps, self.context.completed)

    def start(self) -> None:
        self.context.resume()

    def pause(self) -> None:
        self.context.pause()

    def resume(self) -> None:
        self.context.resume()

    def cancel(self) -> None:
        self.context.cancel()
