"""Serial and parallel workflow scheduling."""

from __future__ import annotations

import asyncio
import inspect
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal, cast

from .executor import Executor
from .task import Step

ScheduleMode = Literal["serial", "parallel"]


class Scheduler:
    """Schedule workflow steps using serial or thread-based parallel execution."""

    def __init__(self, executor: Executor | None = None) -> None:
        self.executor = executor or Executor()

    def run(
        self,
        steps: list[Step],
        context: dict[str, Any],
        mode: ScheduleMode = "serial",
    ) -> list[list[Any]]:
        """Execute steps in the requested scheduling mode."""
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
        semaphore = asyncio.Semaphore(max_parallelism)

        async def execute(step: Step) -> list[Any]:
            async with semaphore:
                if not step.should_run(context):
                    return []
                value = step.task.run(context)
                value = await value if inspect.isawaitable(value) else value
                return [value]

        tasks = [asyncio.create_task(execute(step)) for step in steps]
        if fail_fast:
            try:
                return cast(list[list[Any] | Exception], await asyncio.gather(*tasks))
            except Exception:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                raise
        return cast(
            list[list[Any] | Exception],
            list(await asyncio.gather(*tasks, return_exceptions=True)),
        )
