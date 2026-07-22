"""Validation and reconstruction of workflow runtime checkpoints."""

from __future__ import annotations

from typing import Any

from .checkpoint import Checkpoint
from .control import ExecutionState
from .models import WorkflowContext
from .runtime import ExecutionContext, WorkflowRuntime


class RecoveryError(ValueError):
    """A checkpoint cannot be applied to the supplied workflow definition."""


def restore_runtime(runtime: WorkflowRuntime, checkpoint: Checkpoint) -> None:
    """Restore a runtime's context, queues, result states, and retry counters.

    Steps marked completed or skipped are removed from the dispatch queue. A
    step that was running during a process interruption is returned to the
    queue: it has no terminal result and is therefore unfinished work.
    """
    known = {runtime.step_name(step) for step in runtime.dispatcher.pending}
    referenced = set().union(
        checkpoint.ready,
        checkpoint.waiting,
        checkpoint.running,
        checkpoint.completed,
        checkpoint.failed,
        checkpoint.cancelled,
        checkpoint.skipped,
    )
    unknown = referenced - known
    if unknown:
        names = ", ".join(sorted(unknown))
        raise RecoveryError(f"Checkpoint contains unknown step(s): {names}")
    try:
        state = ExecutionState[checkpoint.state]
    except KeyError as exc:
        raise RecoveryError(f"Unknown execution state: {checkpoint.state}") from exc
    context_data: dict[str, Any] = checkpoint.context
    execution = ExecutionContext(
        workflow=WorkflowContext(
            inputs=dict(context_data.get("inputs", {})),
            shared=dict(context_data.get("shared", {})),
            results=dict(context_data.get("results", {})),
            previous_result=context_data.get("previous_result"),
        ),
        state=state,
        completed=set(checkpoint.completed),
        running=set(checkpoint.running),
        failed=set(checkpoint.failed),
        cancelled=set(checkpoint.cancelled),
        skipped=set(checkpoint.skipped),
        retries=dict(checkpoint.retries),
        step_results=dict(checkpoint.step_results),
    )
    runtime.restore(execution, execution.completed)
