"""Deterministic local coverage for the SDK reference workflow runtime."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from tkai.sdk.memory import ReferenceMemory
from tkai.sdk.workflow import (
    ConditionTask,
    ExecutionContext,
    Node,
    NodeKind,
    ReferenceMemoryTask,
    WorkflowDefinition,
    WorkflowRuntime,
    WorkflowState,
)


def test_task_sequence_context_and_reference_memory_are_explicit() -> None:
    """Task and sequence nodes use only caller-supplied context dependencies."""
    memory = ReferenceMemory()
    definition = WorkflowDefinition(
        "context",
        (
            Node(
                "store", handler=ReferenceMemoryTask("answer", 42), successors=("end",)
            ),
            Node("end", NodeKind.END),
        ),
        "store",
    )
    context = ExecutionContext(memory=memory, provider=object(), agent=object())
    result = WorkflowRuntime(definition).execute(context)

    assert result.state is WorkflowState.SUCCEEDED
    assert result.output == 42
    assert memory.get("answer") is not None
    assert context.provider is not None and context.agent is not None


def test_condition_loop_retry_branch_and_parallel_paths_are_deterministic() -> None:
    """All reference control nodes stay local and use explicit handler outcomes."""
    attempts = 0
    loop_values = iter((True, False))

    def retry(_context: object) -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise RuntimeError("retry locally")
        return "retried"

    definition = WorkflowDefinition(
        "controls",
        (
            Node(
                "condition",
                NodeKind.CONDITION,
                ConditionTask(lambda _context: True),
                ("loop", "end"),
            ),
            Node(
                "loop",
                NodeKind.LOOP,
                lambda _context: next(loop_values),
                ("loop", "retry"),
            ),
            Node("retry", NodeKind.RETRY, retry, ("branch",), {"attempts": 3}),
            Node(
                "branch",
                NodeKind.BRANCH,
                lambda _context: "parallel",
                ("end", "parallel"),
            ),
            Node("parallel", NodeKind.PARALLEL, successors=("left", "right")),
            Node("left", handler=lambda _context: "left"),
            Node("right", handler=lambda _context: "right"),
            Node("end", NodeKind.END),
        ),
        "condition",
    )
    result = WorkflowRuntime(definition).execute()

    assert result.state is WorkflowState.SUCCEEDED
    assert attempts == 3
    assert result.variables["left"] == "left"
    assert result.variables["right"] == "right"
    assert any(event.name == "node_retry" for event in result.events)


def test_cancel_timeout_snapshot_restore_and_failure_are_isolated() -> None:
    """Cancellation, timeouts, snapshots, and failures have stable states."""
    definition = WorkflowDefinition(
        "resume",
        (
            Node("first", handler=lambda _context: "first", successors=("second",)),
            Node("second", handler=lambda _context: "second"),
        ),
        "first",
    )
    runtime = WorkflowRuntime(definition)
    assert runtime.step().state is WorkflowState.RUNNING
    snapshot = runtime.snapshot()
    restored = WorkflowRuntime(definition)
    assert restored.restore(snapshot).state is WorkflowState.RUNNING
    assert restored.resume().state is WorkflowState.SUCCEEDED

    cancelled = WorkflowRuntime(definition)
    cancelled.cancel()
    assert cancelled.step().state is WorkflowState.CANCELLED

    clock_values = iter((0.0, 0.0, 1.0))
    timed_out = WorkflowRuntime(definition, clock=lambda: next(clock_values))
    assert (
        timed_out.execute(ExecutionContext(timeout_seconds=0.5)).state
        is WorkflowState.TIMED_OUT
    )

    failed = WorkflowRuntime(
        WorkflowDefinition(
            "failed", (Node("bad", handler=lambda _context: 1 / 0),), "bad"
        )
    ).execute()
    assert failed.state is WorkflowState.FAILED
    assert isinstance(failed.error, ZeroDivisionError)


def test_runtime_operations_are_thread_safe_and_reference_only() -> None:
    """Concurrent independent executions do not mutate shared runtime state unsafely."""
    definition = WorkflowDefinition(
        "safe", (Node("task", handler=lambda _context: "ok"),), "task"
    )
    runtime = WorkflowRuntime(definition)
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _index: runtime.execute(), range(16)))
    assert all(result.state is WorkflowState.SUCCEEDED for result in results)
