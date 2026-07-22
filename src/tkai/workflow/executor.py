"""Synchronous and asynchronous step execution with retries and timeouts."""

from __future__ import annotations

import asyncio
import inspect
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from typing import Any

from tkai.core.exceptions import WorkflowError

from .events import Event, EventBus
from .models import StepResult, StepStatus
from .task import Step


class StepError(WorkflowError):
    """A step handler failed."""


class RetryError(StepError):
    """A step exhausted retry attempts."""


class ExecutionError(WorkflowError):
    """Workflow execution failed."""


class Executor:
    """Execute a Step while retaining the legacy list-returning interface."""

    def __init__(
        self, events: EventBus | None = None, *, fail_fast_events: bool = False
    ) -> None:
        self.events = events or EventBus()
        self.fail_fast_events = fail_fast_events

    def execute(self, step: Step, context: dict[str, Any]) -> list[Any]:
        result = self.execute_result(step, context)
        if result.status is StepStatus.FAILED:
            raise result.error  # type: ignore[misc]
        return result.output if isinstance(result.output, list) else [result.output]

    def execute_result(self, step: Step, context: dict[str, Any]) -> StepResult:
        if not step.should_run(context):
            return StepResult(
                step.name or step.task.name, StepStatus.SKIPPED, output=[]
            )
        iterations = step.iterable if step.iterable is not None else range(step.loop)
        outputs: list[Any] = []
        for index, item in enumerate(iterations):
            if index >= step.max_iterations or (
                step.loop_condition and not step.loop_condition(context)
            ):
                break
            context["loop_item"] = item
            try:
                outputs.append(self._attempt(step, context))
            except StepError as exc:
                return StepResult(
                    step.name or step.task.name,
                    StepStatus.FAILED,
                    error=exc,
                    attempts=(
                        step.retry.max_attempts if step.retry else step.retries + 1
                    ),
                )
        return StepResult(
            step.name or step.task.name,
            StepStatus.COMPLETED,
            output=outputs,
            attempts=1,
        )

    def _attempt(self, step: Step, context: dict[str, Any]) -> Any:
        policy = (
            step.retry
            or type(
                "P",
                (),
                {
                    "max_attempts": step.retries + 1,
                    "delay": 0.0,
                    "backoff": 1.0,
                    "retry_on": (Exception,),
                },
            )()
        )
        for attempt in range(1, policy.max_attempts + 1):
            self.events.emit(
                Event("step.started", {"step": step.name, "attempt": attempt}),
                fail_fast=self.fail_fast_events,
            )
            self.events.emit(
                Event("task.started", {"task": step.task.name, "attempt": attempt}),
                fail_fast=self.fail_fast_events,
            )
            try:
                value = self._call(step, context)
            except policy.retry_on as exc:
                if attempt == policy.max_attempts:
                    self.events.emit(
                        Event("step.failed", {"step": step.name, "error": str(exc)}),
                        fail_fast=self.fail_fast_events,
                    )
                    self.events.emit(
                        Event(
                            "task.failed", {"task": step.task.name, "error": str(exc)}
                        ),
                        fail_fast=self.fail_fast_events,
                    )
                    raise RetryError(
                        f"Step '{step.name}' failed after {attempt} attempt(s)"
                    ) from exc
                self.events.emit(
                    Event("step.retried", {"step": step.name, "attempt": attempt}),
                    fail_fast=self.fail_fast_events,
                )
                time.sleep(policy.delay * (policy.backoff ** (attempt - 1)))
            else:
                self.events.emit(
                    Event("step.completed", {"step": step.name}),
                    fail_fast=self.fail_fast_events,
                )
                self.events.emit(
                    Event("task.completed", {"task": step.task.name, "result": value}),
                    fail_fast=self.fail_fast_events,
                )
                return value
        raise AssertionError("retry exhausted")

    def _call(self, step: Step, context: dict[str, Any]) -> Any:
        def invoke() -> Any:
            value = step.task.run(context)
            if not inspect.isawaitable(value):
                return value

            async def resolve() -> Any:
                return await value

            return asyncio.run(resolve())

        if step.timeout is None:
            return invoke()
        with ThreadPoolExecutor(max_workers=1) as pool:
            try:
                return pool.submit(invoke).result(timeout=step.timeout)
            except FutureTimeout as exc:
                raise TimeoutError(f"Step '{step.name}' timed out") from exc


WorkflowExecutor = Executor
