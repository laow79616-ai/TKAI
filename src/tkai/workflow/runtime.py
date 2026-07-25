"""Single-owner workflow runtime state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .control import ExecutionState, validate_transition
from .dispatch import Dispatcher
from .models import WorkflowContext
from .task import Step


@dataclass(slots=True)
class ExecutionContext:
    workflow: WorkflowContext = field(default_factory=WorkflowContext)
    state: ExecutionState = ExecutionState.PENDING
    completed: set[str] = field(default_factory=set)
    running: set[str] = field(default_factory=set)
    failed: set[str] = field(default_factory=set)
    cancelled: set[str] = field(default_factory=set)
    skipped: set[str] = field(default_factory=set)
    retries: dict[str, int] = field(default_factory=dict)
    step_results: dict[str, dict[str, Any]] = field(default_factory=dict)

    def pause(self) -> None:
        self.transition(ExecutionState.PAUSING)

    def resume(self) -> None:
        self.transition(ExecutionState.RESUMING)

    def cancel(self) -> None:
        target = (
            ExecutionState.CANCELLED
            if self.state is ExecutionState.PENDING
            else ExecutionState.CANCELLING
        )
        self.transition(target)

    def can_dispatch(self) -> bool:
        return self.state is ExecutionState.RUNNING

    def transition(self, target: ExecutionState) -> None:
        """Apply one validated runtime state transition."""
        validate_transition(self.state, target)
        self.state = target


class WorkflowRuntime:
    def __init__(
        self, steps: list[Step], context: dict[str, Any] | None = None
    ) -> None:
        self.context = ExecutionContext(WorkflowContext(inputs=context or {}))
        self.dispatcher = Dispatcher(steps, self.context.completed)

    def start(self) -> None:
        self.context.transition(ExecutionState.RUNNING)

    def pause(self) -> None:
        """Request a cooperative pause before the next dispatch decision."""
        self.context.pause()

    def resume(self) -> None:
        """Request continued dispatch for a paused runtime."""
        self.context.resume()

    def cancel(self) -> None:
        """Request cancellation and prevent any future dequeue operation."""
        self.context.cancel()

    def checkpoint(self) -> bool:
        """Return whether a handler may continue cooperative work.

        It never forcibly interrupts a handler. A false value means pause or
        cancellation was requested and the handler can safely return early.
        """
        return self.context.state is ExecutionState.RUNNING

    @property
    def pause_requested(self) -> bool:
        """Whether dispatch must stop after current work completes."""
        return self.context.state is ExecutionState.PAUSING

    @property
    def cancel_requested(self) -> bool:
        """Whether dispatch must stop and pending work be cancelled."""
        return self.context.state is ExecutionState.CANCELLING

    def prepare_dispatch(self) -> bool:
        """Resolve control requests at the only point new work may be claimed."""
        if self.context.state is ExecutionState.RESUMING:
            self.context.transition(ExecutionState.RUNNING)
        if self.context.state is ExecutionState.PAUSING:
            if not self.context.running:
                self.context.transition(ExecutionState.PAUSED)
            return False
        return self.context.can_dispatch()

    def complete(self) -> None:
        """Mark a successfully drained runtime as completed."""
        if self.context.state is ExecutionState.RUNNING:
            self.context.transition(ExecutionState.COMPLETED)

    def fail(self) -> None:
        """Mark a running runtime as failed."""
        if self.context.state is ExecutionState.RUNNING:
            self.context.transition(ExecutionState.FAILED)

    def finish_cancel(self) -> None:
        """Mark queued steps cancelled and close a cancellation request."""
        for step in self.dispatcher.cancel_waiting():
            self.context.cancelled.add(self.step_name(step))
        if self.context.state is ExecutionState.CANCELLING and not self.context.running:
            self.context.transition(ExecutionState.CANCELLED)

    def restore(self, context: ExecutionContext, completed: set[str]) -> None:
        """Restore state so dispatcher will not schedule completed steps again."""
        self.context = context
        self.context.completed = set(completed)
        terminal = (
            self.context.completed
            | self.context.skipped
            | self.context.failed
            | self.context.cancelled
        )
        satisfied = self.context.completed | self.context.skipped
        self.dispatcher.restore(terminal, satisfied)

    @staticmethod
    def step_name(step: Step) -> str:
        """Return the stable public name used in queues and snapshots."""
        return step.name or step.task.name
