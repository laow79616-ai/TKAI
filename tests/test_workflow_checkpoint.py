"""Regression tests for runtime snapshots and in-memory recovery."""

from __future__ import annotations

import json
import threading
import time

from tkai.workflow import (
    Checkpoint,
    CheckpointManager,
    Step,
    Task,
    Workflow,
    WorkflowDefinition,
    WorkflowEngine,
    WorkflowStatus,
)
from tkai.workflow.runtime import WorkflowRuntime


def _paused_workflow(definition: WorkflowDefinition) -> Workflow:
    workflow = Workflow(definition)
    workflow.transition(WorkflowStatus.VALIDATED)
    workflow.transition(WorkflowStatus.PENDING)
    workflow.transition(WorkflowStatus.RUNNING)
    workflow.pause()
    return workflow


def test_checkpoint_json_round_trip_contains_all_dispatch_state():
    first = Step(Task("first", lambda _: "one"))
    second = Step(Task("second", lambda _: "two"), dependencies=("first",))
    runtime = WorkflowRuntime([first, second], {"value": 1})
    runtime.start()
    runtime.context.completed.add("first")
    runtime.dispatcher.mark_complete(first)
    runtime.context.failed.add("bad")
    runtime.context.cancelled.add("cancelled")
    runtime.context.skipped.add("skipped")
    runtime.context.running.add("second")
    runtime.context.retries["second"] = 2
    runtime.context.step_results["first"] = {
        "status": "COMPLETED",
        "output": "one",
        "error": None,
        "attempts": 1,
    }

    checkpoint = CheckpointManager().create_checkpoint("demo", runtime)
    decoded = json.loads(checkpoint.to_json())

    assert decoded["completed"] == ["first"]
    assert decoded["ready"] == ["second"]
    assert decoded["waiting"] == []
    assert decoded["running"] == ["second"]
    assert decoded["failed"] == ["bad"]
    assert decoded["cancelled"] == ["cancelled"]
    assert decoded["skipped"] == ["skipped"]
    assert decoded["retries"] == {"second": 2}
    assert Checkpoint.from_json(checkpoint.to_json()) == checkpoint


def test_checkpoint_manager_exports_imports_and_restores_retry_counters():
    step = Step(Task("one", lambda _: 1))
    runtime = WorkflowRuntime([step])
    runtime.start()
    runtime.context.retries["one"] = 3
    manager = CheckpointManager()
    manager.create_checkpoint("source", runtime)
    exported = manager.export_checkpoint("source")
    imported = manager.import_checkpoint("target", exported)

    assert imported.retries == {"one": 3}
    assert manager.load_checkpoint("target") == imported


def test_resume_skips_completed_steps_and_executes_remaining_steps():
    calls: list[str] = []
    first = Step(Task("first", lambda _: calls.append("first") or "first"))

    def run_second(context: dict[str, object]) -> object:
        calls.append("second")
        return context["results"]["first"]

    second = Step(Task("second", run_second), dependencies=("first",))
    definition = WorkflowDefinition("recover", [first, second])
    runtime = WorkflowRuntime(definition.steps)
    runtime.start()
    runtime.context.completed.add("first")
    runtime.context.workflow.results["first"] = ["first"]
    runtime.context.step_results["first"] = {
        "status": "COMPLETED",
        "output": ["first"],
        "error": None,
        "attempts": 1,
    }
    runtime.dispatcher.mark_complete(first)
    checkpoint = CheckpointManager().create_checkpoint("recover", runtime)

    result = WorkflowEngine().resume(_paused_workflow(definition), checkpoint.to_dict())

    assert calls == ["second"]
    assert result.status is WorkflowStatus.COMPLETED
    assert [item.name for item in result.steps] == ["first", "second"]
    assert result.steps[0].output == ["first"]


def test_recovery_preserves_terminal_step_sets_without_rescheduling_them():
    calls: list[str] = []
    done = Step(Task("done", lambda _: calls.append("done")))
    skipped = Step(Task("skipped", lambda _: calls.append("skipped")))
    remaining = Step(Task("remaining", lambda _: calls.append("remaining")))
    definition = WorkflowDefinition("terminal", [done, skipped, remaining])
    runtime = WorkflowRuntime(definition.steps)
    runtime.start()
    runtime.context.completed.add("done")
    runtime.context.skipped.add("skipped")
    runtime.context.step_results["done"] = {
        "status": "COMPLETED",
        "output": [],
        "error": None,
        "attempts": 1,
    }
    runtime.context.step_results["skipped"] = {
        "status": "SKIPPED",
        "output": [],
        "error": None,
        "attempts": 0,
    }
    runtime.dispatcher.mark_complete(done)
    runtime.dispatcher.mark_complete(skipped)
    checkpoint = CheckpointManager().create_checkpoint("terminal", runtime)

    result = WorkflowEngine().resume(_paused_workflow(definition), checkpoint.to_dict())

    assert calls == ["remaining"]
    assert {item.name for item in result.steps} == {"done", "skipped", "remaining"}


def test_resume_runs_remaining_independent_steps_in_parallel():
    first = Step(Task("first", lambda _: "first"))
    active = 0
    peak = 0
    lock = threading.Lock()

    def concurrent(_: dict[str, object]) -> str:
        nonlocal active, peak
        with lock:
            active += 1
            peak = max(peak, active)
        time.sleep(0.01)
        with lock:
            active -= 1
        return "done"

    second = Step(Task("second", concurrent), dependencies=("first",))
    third = Step(Task("third", concurrent), dependencies=("first",))
    definition = WorkflowDefinition("parallel-recover", [first, second, third])
    runtime = WorkflowRuntime(definition.steps)
    runtime.start()
    runtime.context.completed.add("first")
    runtime.context.workflow.results["first"] = ["first"]
    runtime.context.step_results["first"] = {
        "status": "COMPLETED",
        "output": ["first"],
        "error": None,
        "attempts": 1,
    }
    runtime.dispatcher.mark_complete(first)
    checkpoint = CheckpointManager().create_checkpoint("parallel", runtime)

    result = WorkflowEngine().resume(
        _paused_workflow(definition),
        checkpoint.to_dict(),
        mode="parallel",
        max_parallelism=2,
    )

    assert result.status is WorkflowStatus.COMPLETED
    assert peak == 2
