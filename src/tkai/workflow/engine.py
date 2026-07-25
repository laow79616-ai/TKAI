"""High-level workflow orchestration API."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from functools import partial
from typing import Any

from tkai.core.exceptions import WorkflowError

from .checkpoint import Checkpoint, CheckpointManager
from .control import ExecutionState
from .events import EventBus
from .executor import Executor
from .models import (
    Workflow,
    WorkflowContext,
    WorkflowDefinition,
    WorkflowResult,
    WorkflowStatus,
)
from .recovery import restore_runtime
from .runtime import WorkflowRuntime
from .scheduler import ScheduleMode, Scheduler
from .task import Step


class WorkflowEngine:
    """Execute workflow steps with shared context and lifecycle events."""

    def __init__(self, events: EventBus | None = None) -> None:
        self.events = events or EventBus()
        self.executor = Executor(self.events)
        self.scheduler = Scheduler(self.executor)
        self.checkpoints = CheckpointManager()
        self.last_checkpoint: Checkpoint | None = None

    def create_runtime(
        self,
        definition: WorkflowDefinition,
        inputs: dict[str, Any] | None = None,
    ) -> WorkflowRuntime:
        """Create a controllable runtime without changing legacy execution APIs."""
        runtime = WorkflowRuntime(definition.steps, inputs)
        runtime.start()
        return runtime

    def pause(self, runtime: WorkflowRuntime, name: str = "workflow") -> Checkpoint:
        """Request a pause and capture the resulting cooperative checkpoint."""
        runtime.pause()
        runtime.prepare_dispatch()
        checkpoint = self.checkpoints.create_checkpoint(name, runtime)
        self.last_checkpoint = checkpoint
        return checkpoint

    def cancel(self, runtime: WorkflowRuntime, name: str = "workflow") -> Checkpoint:
        """Request cancellation and capture pending work before it is drained."""
        runtime.cancel()
        runtime.finish_cancel()
        checkpoint = self.checkpoints.create_checkpoint(name, runtime)
        self.last_checkpoint = checkpoint
        return checkpoint

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
        runtime = WorkflowRuntime(steps, context)
        runtime.start()
        return await self.run_runtime_async(
            runtime,
            max_parallelism=max_parallelism,
            fail_fast=fail_fast,
        )

    async def run_runtime_async(
        self,
        runtime: WorkflowRuntime,
        *,
        max_parallelism: int = 4,
        fail_fast: bool = True,
    ) -> list[list[Any] | Exception]:
        """Run an externally controllable runtime using asyncio dispatch."""
        results = await self.scheduler.run_runtime_async(
            runtime,
            max_parallelism=max_parallelism,
            fail_fast=fail_fast,
        )
        if runtime.context.state in (ExecutionState.PAUSED, ExecutionState.CANCELLED):
            self.last_checkpoint = self.checkpoints.create_checkpoint(
                "workflow", runtime
            )
        return results

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

    def resume(
        self,
        workflow: Workflow,
        snapshot: dict[str, Any] | None = None,
        *,
        runtime: WorkflowRuntime | None = None,
        mode: ScheduleMode = "serial",
        max_parallelism: int = 4,
        fail_fast: bool = True,
    ) -> WorkflowResult:
        """Resume a paused workflow from a full runtime checkpoint.

        This additive compatibility API still accepts old context-only
        snapshots. Full checkpoints restore dispatcher state so terminal steps
        are never invoked again.
        """
        if runtime is None:
            if snapshot is None:
                raise ValueError("A snapshot or paused runtime is required to resume")
            checkpoint = self._checkpoint_from_snapshot(snapshot)
            runtime = WorkflowRuntime(workflow.definition.steps)
            restore_runtime(runtime, checkpoint)
        if workflow.status is WorkflowStatus.PAUSED:
            workflow.resume()
        elif workflow.status is not WorkflowStatus.RUNNING:
            raise ValueError("Only a running or paused workflow can be resumed")
        if runtime.context.state is ExecutionState.PAUSED:
            runtime.resume()
        return self._execute_runtime(
            workflow,
            runtime,
            mode=mode,
            max_parallelism=max_parallelism,
            fail_fast=fail_fast,
        )

    @staticmethod
    def _checkpoint_from_snapshot(snapshot: dict[str, Any]) -> Checkpoint:
        """Upgrade legacy ``Workflow.snapshot`` payloads to a checkpoint."""
        if "state" in snapshot:
            return Checkpoint.from_dict(snapshot)
        context = snapshot.get("context", {})
        return Checkpoint(
            context=context,
            state="PAUSED",
            completed=sorted(context.get("results", {})),
        )

    def _execute_runtime(
        self,
        workflow: Workflow,
        runtime: WorkflowRuntime,
        *,
        mode: ScheduleMode = "serial",
        max_parallelism: int = 4,
        fail_fast: bool = True,
    ) -> WorkflowResult:
        """Drive a recovered runtime without revisiting its terminal steps."""
        if mode not in ("serial", "parallel"):
            raise ValueError(f"Unknown schedule mode: {mode}")
        if max_parallelism < 1:
            raise ValueError("max_parallelism must be at least one")
        result_by_name = self._restored_results(runtime)
        try:
            while runtime.dispatcher.pending:
                if runtime.cancel_requested:
                    runtime.finish_cancel()
                    if workflow.status in (
                        WorkflowStatus.RUNNING,
                        WorkflowStatus.PAUSED,
                    ):
                        workflow.cancel()
                    checkpoint = self.checkpoints.create_checkpoint(
                        workflow.definition.name, runtime
                    )
                    self.last_checkpoint = checkpoint
                    return WorkflowResult(
                        workflow.definition.name,
                        workflow.status,
                        self._ordered_results(workflow, result_by_name),
                        runtime.context.workflow.previous_result,
                    )
                if not runtime.prepare_dispatch():
                    if runtime.context.state is ExecutionState.PAUSED:
                        if workflow.status is WorkflowStatus.RUNNING:
                            workflow.pause()
                        checkpoint = self.checkpoints.create_checkpoint(
                            workflow.definition.name, runtime
                        )
                        self.last_checkpoint = checkpoint
                        return WorkflowResult(
                            workflow.definition.name,
                            workflow.status,
                            self._ordered_results(workflow, result_by_name),
                            runtime.context.workflow.previous_result,
                        )
                    break
                ready = runtime.dispatcher.next_ready()
                if not ready:
                    raise WorkflowError("Circular or blocked step dependency detected")
                batch = ready[:1] if mode == "serial" else ready[:max_parallelism]
                for step in batch:
                    runtime.dispatcher.claim(step)
                    runtime.context.running.add(runtime.step_name(step))
                context = runtime.context.workflow
                if mode == "parallel" and len(batch) > 1:
                    execute_step = partial(
                        self.executor.execute_result, context=context.data()
                    )
                    with ThreadPoolExecutor(max_workers=max_parallelism) as pool:
                        step_results = list(pool.map(execute_step, batch))
                else:
                    step_results = [
                        self.executor.execute_result(step, context.data())
                        for step in batch
                    ]
                for step, step_result in zip(batch, step_results, strict=True):
                    name = step_result.name
                    runtime.context.running.discard(name)
                    result_by_name[name] = step_result
                    runtime.context.step_results[name] = self._step_result_data(
                        step_result
                    )
                    runtime.context.retries[name] = step_result.attempts
                    if step_result.status.name == "COMPLETED":
                        runtime.context.completed.add(name)
                        runtime.dispatcher.mark_complete(step)
                        context.results[name] = step_result.output
                        context.previous_result = step_result.output
                    elif step_result.status.name == "SKIPPED":
                        runtime.context.skipped.add(name)
                        runtime.dispatcher.mark_complete(step)
                    else:
                        runtime.context.failed.add(name)
                        runtime.dispatcher.mark_terminal(step)
                        if fail_fast and not step.continue_on_error:
                            raise step_result.error or WorkflowError(
                                f"Step '{name}' failed"
                            )
                        if step.continue_on_error:
                            runtime.dispatcher.completed.add(name)
                if runtime.context.failed and fail_fast:
                    break
            runtime.prepare_dispatch()
            if runtime.cancel_requested:
                runtime.finish_cancel()
            if runtime.context.state is ExecutionState.CANCELLED:
                if workflow.status in (WorkflowStatus.RUNNING, WorkflowStatus.PAUSED):
                    workflow.cancel()
                self.last_checkpoint = self.checkpoints.create_checkpoint(
                    workflow.definition.name, runtime
                )
                return WorkflowResult(
                    workflow.definition.name,
                    workflow.status,
                    self._ordered_results(workflow, result_by_name),
                    runtime.context.workflow.previous_result,
                )
            if runtime.context.state is ExecutionState.PAUSED:
                if workflow.status is WorkflowStatus.RUNNING:
                    workflow.pause()
                self.last_checkpoint = self.checkpoints.create_checkpoint(
                    workflow.definition.name, runtime
                )
            elif runtime.context.failed:
                runtime.fail()
                workflow.transition(WorkflowStatus.FAILED)
            else:
                runtime.complete()
                workflow.transition(WorkflowStatus.COMPLETED)
            return WorkflowResult(
                workflow.definition.name,
                workflow.status,
                self._ordered_results(workflow, result_by_name),
                runtime.context.workflow.previous_result,
            )
        except Exception as exc:
            runtime.fail()
            if workflow.status is WorkflowStatus.RUNNING:
                workflow.transition(WorkflowStatus.FAILED)
            return WorkflowResult(
                workflow.definition.name,
                workflow.status,
                self._ordered_results(workflow, result_by_name),
                error=exc,
            )

    @staticmethod
    def _step_result_data(result: Any) -> dict[str, Any]:
        """Store the public result model in checkpoint-safe form."""
        return {
            "status": result.status.name,
            "output": result.output,
            "error": str(result.error) if result.error else None,
            "attempts": result.attempts,
        }

    @staticmethod
    def _restored_results(runtime: WorkflowRuntime) -> dict[str, Any]:
        """Return reconstructed terminal results retained by a checkpoint."""
        from .models import StepResult, StepStatus

        results: dict[str, Any] = {}
        for name, item in runtime.context.step_results.items():
            status = StepStatus[item["status"]]
            results[name] = StepResult(
                name,
                status,
                output=item.get("output"),
                error=Exception(item["error"]) if item.get("error") else None,
                attempts=int(item.get("attempts", 0)),
            )
        return results

    @staticmethod
    def _ordered_results(workflow: Workflow, results: dict[str, Any]) -> list[Any]:
        """Keep externally visible results in definition order after recovery."""
        return [
            results[name]
            for name in (step.name for step in workflow.definition.steps)
            if name in results
        ]
