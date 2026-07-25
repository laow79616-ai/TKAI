"""Serial and parallel workflow scheduling compatibility facade."""

from __future__ import annotations

import asyncio
import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal, cast

from .control import ExecutionState
from .executor import Executor
from .runtime import WorkflowRuntime
from .task import Step

ScheduleMode = Literal["serial", "parallel"]


class Scheduler:
    """Schedule legacy work and delegate controlled async work to a runtime."""

    def __init__(self, executor: Executor | None = None) -> None:
        self.executor = executor or Executor()

    def run(
        self,
        steps: list[Step],
        context: dict[str, Any],
        mode: ScheduleMode = "serial",
    ) -> list[list[Any]]:
        """Execute legacy steps in the requested scheduling mode."""
        if mode == "serial":
            return [self.executor.execute(step, context) for step in steps]
        with ThreadPoolExecutor(max_workers=len(steps) or 1) as pool:
            return list(
                pool.map(lambda step: self.executor.execute(step, context), steps)
            )

    async def run_async(
        self,
        steps: list[Step],
        context: dict[str, Any],
        *,
        max_parallelism: int = 4,
        fail_fast: bool = True,
    ) -> list[list[Any] | Exception]:
        """Run independent steps concurrently with stable input-order results."""
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
        """Dispatch a runtime cooperatively using native asyncio tasks.

        A step is claimed before its task is created. Pause and cancellation are
        inspected before every claim, so no additional task is started after a
        control request. Results are assigned by definition index rather than
        completion order.
        """
        if max_parallelism < 1:
            raise ValueError("max_parallelism must be at least one")
        if runtime.context.state is ExecutionState.PENDING:
            runtime.start()
        steps = list(runtime.dispatcher.pending)
        order = {runtime.step_name(step): index for index, step in enumerate(steps)}
        results: list[list[Any] | Exception | None] = [None] * len(steps)
        active: dict[asyncio.Task[list[Any]], Step] = {}

        async def invoke(step: Step) -> list[Any]:
            context = runtime.context.workflow.data()
            if not step.should_run(context):
                return []
            value = step.task.run(context)
            value = await value if inspect.isawaitable(value) else value
            return value if isinstance(value, list) else [value]

        def record(step: Step, value: list[Any] | Exception) -> None:
            name = runtime.step_name(step)
            results[order[name]] = value
            runtime.context.running.discard(name)
            if isinstance(value, Exception):
                runtime.context.failed.add(name)
                runtime.dispatcher.mark_terminal(step)
                return
            if not step.should_run(runtime.context.workflow.data()):
                runtime.context.skipped.add(name)
            else:
                runtime.context.completed.add(name)
                runtime.context.workflow.results[name] = value
                runtime.context.workflow.previous_result = value
            runtime.dispatcher.mark_complete(step)

        while runtime.dispatcher.pending or active:
            if runtime.cancel_requested:
                for task in active:
                    task.cancel()
                cancelled = await asyncio.gather(*active, return_exceptions=True)
                for task, _outcome in zip(active, cancelled, strict=True):
                    step = active[task]
                    name = runtime.step_name(step)
                    runtime.context.running.discard(name)
                    runtime.context.cancelled.add(name)
                    runtime.dispatcher.mark_terminal(step)
                    results[order[name]] = []
                active.clear()
                runtime.finish_cancel()
                break

            if not runtime.prepare_dispatch():
                if runtime.context.state is ExecutionState.PAUSED and not active:
                    break
                if not active:
                    break
            while (
                runtime.prepare_dispatch()
                and len(active) < max_parallelism
                and (ready := runtime.dispatcher.next_ready())
            ):
                step = ready[0]
                runtime.dispatcher.claim(step)
                runtime.context.running.add(runtime.step_name(step))
                active[asyncio.create_task(invoke(step))] = step

            if not active:
                if runtime.dispatcher.pending and runtime.prepare_dispatch():
                    runtime.fail()
                    raise ValueError("Circular or blocked step dependency detected")
                continue
            done, _ = await asyncio.wait(active, return_when=asyncio.FIRST_COMPLETED)
            for task in done:
                step = active.pop(task)
                try:
                    record(step, task.result())
                except asyncio.CancelledError:
                    name = runtime.step_name(step)
                    runtime.context.running.discard(name)
                    runtime.context.cancelled.add(name)
                    runtime.dispatcher.mark_terminal(step)
                    results[order[name]] = []
                except Exception as exc:
                    record(step, exc)
                    if fail_fast:
                        for pending_task in active:
                            pending_task.cancel()
                        await asyncio.gather(*active, return_exceptions=True)
                        runtime.fail()
                        raise

        if not runtime.dispatcher.pending and not active:
            runtime.complete()
        return cast(list[list[Any] | Exception], [item or [] for item in results])
