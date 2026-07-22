"""High-level workflow orchestration API."""

from __future__ import annotations

from typing import Any

from tkai.core.exceptions import WorkflowError

from .events import EventBus
from .executor import Executor
from .models import (
    Workflow,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowStatus,
)
from .scheduler import ScheduleMode, Scheduler
from .task import Step


class WorkflowEngine:
    """Execute workflow steps with shared context and lifecycle events."""

    def __init__(self, events: EventBus | None = None) -> None:
        self.events = events or EventBus()
        self.executor = Executor(self.events)
        self.scheduler = Scheduler(self.executor)

    def run(
        self,
        steps: list[Step],
        context: dict[str, Any] | None = None,
        mode: ScheduleMode = "serial",
    ) -> list[list[Any]]:
        """Run steps and return their results grouped by step."""
        return self.scheduler.run(steps, context or {}, mode)

    async def run_async(
        self,
        steps: list[Step],
        context: dict[str, Any] | None = None,
        *,
        max_parallelism: int = 4,
        fail_fast: bool = True,
    ) -> list[list[Any] | Exception]:
        """Execute independent steps with native asyncio concurrency."""
        return await self.scheduler.run_async(
            steps,
            context or {},
            max_parallelism=max_parallelism,
            fail_fast=fail_fast,
        )

    def execute(
        self, definition: WorkflowDefinition, inputs: dict[str, Any] | None = None
    ) -> WorkflowResult:
        """Run a named definition serially with dependency validation."""
        workflow = Workflow(definition)
        workflow.transition(WorkflowStatus.VALIDATED)
        workflow.transition(WorkflowStatus.PENDING)
        workflow.transition(WorkflowStatus.RUNNING)
        context = WorkflowContext(inputs=inputs or {})
        known = {step.name for step in definition.steps}
        if any(not set(step.dependency_names) <= known for step in definition.steps):
            workflow.transition(WorkflowStatus.FAILED)
            return WorkflowResult(
                definition.name,
                workflow.status,
                error=ValueError("Missing step dependency"),
            )
        pending = list(definition.steps)
        results = []
        try:
            while pending:
                ready = [
                    step
                    for step in pending
                    if set(step.dependency_names) <= set(context.results)
                ]
                if not ready:
                    raise WorkflowError("Circular step dependency detected")
                for step in ready:
                    result = self.executor.execute_result(step, context.data())
                    results.append(result)
                    pending.remove(step)
                    context.results[result.name] = result.output
                    context.previous_result = result.output
                    if result.status.name == "FAILED" and not step.continue_on_error:
                        raise result.error  # type: ignore[misc]
            workflow.transition(WorkflowStatus.COMPLETED)
            return WorkflowResult(
                definition.name, workflow.status, results, context.previous_result
            )
        except Exception as exc:
            workflow.transition(WorkflowStatus.FAILED)
            return WorkflowResult(definition.name, workflow.status, results, error=exc)
