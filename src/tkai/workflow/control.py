"""Validated cooperative control signals for a workflow runtime."""

from __future__ import annotations

from enum import Enum, auto


class ExecutionState(Enum):
    """The internal lifecycle of a single workflow execution."""

    PENDING = auto()
    RUNNING = auto()
    PAUSING = auto()
    PAUSED = auto()
    RESUMING = auto()
    CANCELLING = auto()
    CANCELLED = auto()
    COMPLETED = auto()
    FAILED = auto()


class ExecutionTransitionError(ValueError):
    """Raised when a runtime control operation is invalid in its current state."""


_TRANSITIONS: dict[ExecutionState, set[ExecutionState]] = {
    ExecutionState.PENDING: {ExecutionState.RUNNING, ExecutionState.CANCELLED},
    ExecutionState.RUNNING: {
        ExecutionState.PAUSING,
        ExecutionState.CANCELLING,
        ExecutionState.COMPLETED,
        ExecutionState.FAILED,
    },
    ExecutionState.PAUSING: {ExecutionState.PAUSED, ExecutionState.CANCELLING},
    ExecutionState.PAUSED: {ExecutionState.RESUMING, ExecutionState.CANCELLING},
    ExecutionState.RESUMING: {ExecutionState.RUNNING, ExecutionState.CANCELLING},
    ExecutionState.CANCELLING: {ExecutionState.CANCELLED},
    ExecutionState.CANCELLED: set(),
    ExecutionState.COMPLETED: set(),
    ExecutionState.FAILED: set(),
}


def validate_transition(current: ExecutionState, target: ExecutionState) -> None:
    """Raise a descriptive error unless ``current`` may transition to ``target``."""
    if target not in _TRANSITIONS[current]:
        raise ExecutionTransitionError(
            f"Illegal execution transition: {current.name} -> {target.name}"
        )
