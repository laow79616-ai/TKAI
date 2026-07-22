"""Serial and parallel workflow scheduling."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Literal

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
