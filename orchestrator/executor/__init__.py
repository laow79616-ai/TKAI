"""Sequential, parallel-ready, conditional, cancellable plan execution."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any
from uuid import uuid4

from ..checkpoints import Checkpoint, CheckpointStore
from ..events import EventBus
from ..metrics import OrchestratorMetrics
from ..models import Execution, ExecutionPlan, ExecutionState, PlanStep
from ..policies import PolicySet
from ..router import Router


class Executor:
    def __init__(
        self,
        router: Router,
        checkpoints: CheckpointStore,
        events: EventBus,
        metrics: OrchestratorMetrics,
        policies: PolicySet,
    ) -> None:
        self.router = router
        self.checkpoints = checkpoints
        self.events = events
        self.metrics = metrics
        self.policies = policies

    def run(
        self,
        plan: ExecutionPlan,
        execution: Execution,
        context: dict[str, Any],
        *,
        start_at: int = 0,
        condition: Callable[[PlanStep, dict[str, Any]], bool] | None = None,
    ) -> Execution:
        execution.state = ExecutionState.RUNNING
        self.events.publish("execution.started", execution_id=execution.id)
        completed = set(execution.results)
        for index, step in enumerate(plan.steps[start_at:], start=start_at):
            if execution.cancelled:
                execution.state = ExecutionState.CANCELLED
                return execution
            if not set(step.dependencies) <= completed:
                raise RuntimeError("Step dependencies are incomplete.")
            if condition is not None and not condition(step, context):
                continue
            for attempt in range(self.policies.retry.attempts):
                execution.attempts += 1
                try:
                    execution.results[step.id] = self.router.resolve(step)(
                        step, context
                    )
                    completed.add(step.id)
                    checkpoint = Checkpoint(
                        str(uuid4()),
                        execution.id,
                        execution.scope.tenant,
                        index + 1,
                        execution.results,
                    )
                    self.checkpoints.save(checkpoint)
                    execution.checkpoint_id = checkpoint.id
                    self.metrics.increment("checkpoint_total")
                    break
                except Exception:
                    if attempt + 1 >= self.policies.retry.attempts:
                        raise
                    self.metrics.increment("execution_retry_total")
        execution.state = ExecutionState.COMPLETED
        self.events.publish("execution.completed", execution_id=execution.id)
        return execution
