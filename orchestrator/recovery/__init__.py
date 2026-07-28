"""Failure recovery, resume, checkpoint restore, rollback, and compensation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..checkpoints import CheckpointStore
from ..models import Execution, ExecutionState


class RecoveryManager:
    def __init__(self, checkpoints: CheckpointStore) -> None:
        self.checkpoints = checkpoints
        self._compensations: dict[str, Callable[[Any], None]] = {}

    def register_compensation(
        self, step_id: str, callback: Callable[[Any], None]
    ) -> None:
        self._compensations[step_id] = callback

    def restore(self, execution: Execution, checkpoint_id: str) -> int:
        checkpoint = self.checkpoints.get(checkpoint_id, execution.scope.tenant)
        execution.results = dict(checkpoint.state)
        execution.checkpoint_id = checkpoint.id
        execution.state = ExecutionState.PAUSED
        return checkpoint.step

    def rollback(self, execution: Execution) -> Execution:
        for step_id, result in reversed(tuple(execution.results.items())):
            callback = self._compensations.get(step_id)
            if callback is not None:
                callback(result)
        execution.results.clear()
        execution.state = ExecutionState.ROLLED_BACK
        return execution
