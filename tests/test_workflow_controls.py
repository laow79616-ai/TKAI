"""Focused tests for cooperative runtime pause, resume, and cancellation."""

from __future__ import annotations

import asyncio

import pytest

from tkai.workflow import (
    ExecutionContext,
    Step,
    Task,
    Workflow,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowStatus,
)
from tkai.workflow.control import ExecutionState, ExecutionTransitionError
from tkai.workflow.runtime import WorkflowRuntime


def _running_workflow(definition: WorkflowDefinition) -> Workflow:
    workflow = Workflow(definition)
    workflow.transition(WorkflowStatus.VALIDATED)
    workflow.transition(WorkflowStatus.PENDING)
    workflow.transition(WorkflowStatus.RUNNING)
    return workflow


def test_execution_state_validates_legal_and_illegal_transitions():
    context = ExecutionContext()
    context.transition(ExecutionState.RUNNING)
    context.transition(ExecutionState.PAUSING)
    context.transition(ExecutionState.PAUSED)
    context.transition(ExecutionState.RESUMING)
    context.transition(ExecutionState.RUNNING)

    with pytest.raises(ExecutionTransitionError, match="PENDING -> COMPLETED"):
        ExecutionContext().transition(ExecutionState.COMPLETED)


def test_pause_stops_new_sync_dispatch_and_creates_checkpoint():
    calls: list[str] = []
    runtime: WorkflowRuntime

    def first(_: dict[str, object]) -> str:
        calls.append("first")
        runtime.pause()
        assert not runtime.checkpoint()
        return "first"

    definition = WorkflowDefinition(
        "paused", [Step(Task("first", first)), Step(Task("second", lambda _: "two"))]
    )
    engine = WorkflowEngine()
    runtime = engine.create_runtime(definition)
    workflow = _running_workflow(definition)

    result = engine._execute_runtime(workflow, runtime)

    assert result.status is WorkflowStatus.PAUSED
    assert calls == ["first"]
    assert runtime.context.state is ExecutionState.PAUSED
    assert [runtime.step_name(step) for step in runtime.dispatcher.pending] == [
        "second"
    ]
    assert engine.last_checkpoint is not None
    assert engine.last_checkpoint.ready == ["second"]


def test_resume_from_live_pause_continues_without_repeating_completed_step():
    calls: list[str] = []
    runtime: WorkflowRuntime

    def first(_: dict[str, object]) -> str:
        calls.append("first")
        runtime.pause()
        return "first"

    definition = WorkflowDefinition(
        "live-resume",
        [
            Step(Task("first", first)),
            Step(Task("second", lambda _: calls.append("second"))),
        ],
    )
    engine = WorkflowEngine()
    runtime = engine.create_runtime(definition)
    workflow = _running_workflow(definition)
    engine._execute_runtime(workflow, runtime)
    result = engine.resume(workflow, runtime=runtime)

    assert result.status is WorkflowStatus.COMPLETED
    assert calls == ["first", "second"]


def test_cancel_stops_future_sync_dispatch_and_preserves_completed_results():
    calls: list[str] = []
    runtime: WorkflowRuntime

    def first(_: dict[str, object]) -> str:
        calls.append("first")
        runtime.cancel()
        return "done"

    definition = WorkflowDefinition(
        "cancel",
        [
            Step(Task("first", first)),
            Step(Task("second", lambda _: calls.append("second"))),
        ],
    )
    engine = WorkflowEngine()
    runtime = engine.create_runtime(definition)

    result = engine._execute_runtime(_running_workflow(definition), runtime)

    assert result.status is WorkflowStatus.CANCELLED
    assert calls == ["first"]
    assert runtime.context.completed == {"first"}
    assert runtime.context.cancelled == {"second"}
    assert engine.last_checkpoint is not None
    assert engine.last_checkpoint.cancelled == ["second"]


def test_cancel_request_on_final_running_step_is_still_cancelled():
    runtime: WorkflowRuntime

    def last(_: dict[str, object]) -> str:
        runtime.cancel()
        return "last"

    definition = WorkflowDefinition("last-cancel", [Step(Task("last", last))])
    engine = WorkflowEngine()
    runtime = engine.create_runtime(definition)

    result = engine._execute_runtime(_running_workflow(definition), runtime)

    assert result.status is WorkflowStatus.CANCELLED
    assert runtime.context.completed == {"last"}


def test_async_parallel_pause_does_not_start_waiting_step():
    calls: list[str] = []
    runtime: WorkflowRuntime

    async def first(_: dict[str, object]) -> str:
        calls.append("first")
        runtime.pause()
        await asyncio.sleep(0)
        return "one"

    async def second(_: dict[str, object]) -> str:
        calls.append("second")
        return "two"

    async def third(_: dict[str, object]) -> str:
        calls.append("third")
        return "three"

    runtime = WorkflowRuntime(
        [
            Step(Task("first", first)),
            Step(Task("second", second)),
            Step(Task("third", third)),
        ]
    )
    runtime.start()
    engine = WorkflowEngine()
    results = asyncio.run(engine.run_runtime_async(runtime, max_parallelism=2))

    assert results == [["one"], ["two"], []]
    assert calls == ["first", "second"]
    assert runtime.context.state is ExecutionState.PAUSED
    assert engine.last_checkpoint is not None
    assert engine.last_checkpoint.ready == ["third"]


def test_async_cancel_cancels_active_tasks_and_waiting_steps():
    started = asyncio.Event()
    cancelled = False
    runtime: WorkflowRuntime

    async def control(_: dict[str, object]) -> str:
        await started.wait()
        runtime.cancel()
        return "control"

    async def slow(_: dict[str, object]) -> str:
        nonlocal cancelled
        started.set()
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            cancelled = True
            raise
        return "slow"

    runtime = WorkflowRuntime(
        [
            Step(Task("control", control)),
            Step(Task("slow", slow)),
            Step(Task("waiting", lambda _: "waiting")),
        ]
    )
    runtime.start()
    engine = WorkflowEngine()
    asyncio.run(engine.run_runtime_async(runtime, max_parallelism=2))

    assert cancelled
    assert runtime.context.state is ExecutionState.CANCELLED
    assert runtime.context.cancelled == {"slow", "waiting"}
    assert engine.last_checkpoint is not None
    assert engine.last_checkpoint.cancelled == ["slow", "waiting"]


def test_async_fail_fast_cancels_remaining_task_without_becoming_control_cancel():
    cancelled = False

    async def bad(_: dict[str, object]) -> None:
        await asyncio.sleep(0)
        raise RuntimeError("boom")

    async def slow(_: dict[str, object]) -> None:
        nonlocal cancelled
        try:
            await asyncio.sleep(1)
        except asyncio.CancelledError:
            cancelled = True
            raise

    runtime = WorkflowRuntime([Step(Task("bad", bad)), Step(Task("slow", slow))])
    runtime.start()
    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(
            WorkflowEngine().scheduler.run_runtime_async(runtime, max_parallelism=2)
        )

    assert cancelled
    assert runtime.context.state is ExecutionState.FAILED
