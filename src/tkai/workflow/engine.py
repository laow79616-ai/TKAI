"""High-level workflow orchestration API."""

from __future__ import annotations

from typing import Any

from .events import EventBus
from .executor import Executor
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
