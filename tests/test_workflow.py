import pytest

from tkai.core.exceptions import WorkflowError
from tkai.workflow import EventBus, Step, Task, WorkflowEngine


def test_serial_condition_loop_and_events():
    received = []
    events = EventBus()
    events.subscribe("task.completed", received.append)
    engine = WorkflowEngine(events)
    context = {"values": []}

    append = Task("append", lambda ctx: ctx["values"].append("ok"))
    skipped = Task("skipped", lambda ctx: ctx["values"].append("no"))

    results = engine.run(
        [Step(append, loop=2), Step(skipped, condition=lambda _: False)], context
    )

    assert context["values"] == ["ok", "ok"]
    assert results == [[None, None], []]
    assert len(received) == 2


def test_parallel_and_retry():
    engine = WorkflowEngine()
    attempts = {"count": 0}

    def flaky(_: dict[str, object]) -> str:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("temporary")
        return "done"

    results = engine.run(
        [Step(Task("first", lambda _: 1)), Step(Task("flaky", flaky), retries=1)],
        mode="parallel",
    )

    assert {tuple(result) for result in results} == {(1,), ("done",)}
    assert attempts["count"] == 2


def test_retry_failure_is_wrapped():
    engine = WorkflowEngine()

    with pytest.raises(WorkflowError, match="failed after 2"):
        engine.run([Step(Task("bad", lambda _: 1 / 0), retries=1)])
