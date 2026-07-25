"""Bounded thread-safety coverage for local V1.2 subsystems."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from threading import Barrier, Lock

from benchmarks.combined_runtime import CombinedRuntimeBenchmark
from benchmarks.policy import _StaticPolicy
from tkai.adaptive import AdaptiveRoutingManager, ProviderSignal
from tkai.distributed import LocalBackend
from tkai.multiregion import MultiRegionManager, Region
from tkai.observability import Event, EventBus
from tkai.policy import PolicyContext, PolicyManager, PolicyStage
from tkai.retry import RetryPolicy
from tkai.telemetry import Metric, TelemetryManager


def test_local_managers_complete_bounded_concurrent_operations() -> None:
    """Exercise policy, telemetry, routing, regions, and backend concurrently."""
    operations = 72
    policy = PolicyManager()
    policy.register(_StaticPolicy("concurrent", True))
    telemetry = TelemetryManager()
    telemetry.start()
    adaptive = AdaptiveRoutingManager()
    adaptive.record_signal(
        ProviderSignal("local", datetime.now(timezone.utc), latency_ms=1.0)
    )
    regions = MultiRegionManager()
    regions.register_region(Region("local", priority=1, latency_estimate_ms=1))
    backend = LocalBackend()
    barrier = Barrier(8)

    def operate(number: int) -> tuple[str, str]:
        if number < 8:
            barrier.wait(timeout=5)
        context = PolicyContext(PolicyStage.BEFORE_REQUEST, {"request_id": str(number)})
        assert policy.execute(context)[0].outcome == "executed"
        telemetry.record(Metric("thread.request", 1, labels={"id": str(number)}))
        assert adaptive.rank_providers(("local",))[0].provider == "local"
        assert regions.select_region().selected_region == "local"
        key = f"request-{number}"
        backend.set(key, number)
        assert backend.get(key) == number
        assert backend.delete(key)
        return context.data["request_id"], key

    with ThreadPoolExecutor(max_workers=8) as executor:
        completed = list(executor.map(operate, range(operations)))

    assert {request_id for request_id, _key in completed} == {
        str(number) for number in range(operations)
    }
    assert len(telemetry.metrics.snapshot()) == operations
    assert len(adaptive.history.snapshot("local")) <= 100
    assert backend.get("request-0") is None


def test_event_bus_multithreaded_publish_isolated_and_exact() -> None:
    """Deliver every event to normal subscribers despite a failing subscriber."""
    producers = 6
    per_producer = 40
    expected = producers * per_producer
    bus = EventBus()
    received: list[str] = []
    received_lock = Lock()

    def normal(event: Event) -> None:
        with received_lock:
            received.append(str(event.data["id"]))

    def failing(event: Event) -> None:
        del event
        raise RuntimeError("isolated")

    bus.subscribe(normal)
    bus.subscribe(failing)

    def publish(producer: int) -> None:
        for sequence in range(per_producer):
            identifier = f"{producer}:{sequence}"
            bus.publish(Event("stress", data={"id": identifier}))

    with ThreadPoolExecutor(max_workers=producers) as executor:
        futures = [executor.submit(publish, producer) for producer in range(producers)]
        for future in futures:
            future.result(timeout=10)

    assert len(bus.events) == len(received) == expected
    assert set(received) == {
        f"{producer}:{sequence}"
        for producer in range(producers)
        for sequence in range(per_producer)
    }
    bus.unsubscribe(normal)
    bus.unsubscribe(failing)
    bus.clear()
    assert bus.events == []


def test_retry_budgets_and_local_locks_remain_bounded_in_threads() -> None:
    """Retry budgets are operation-local while every acquired local lock releases."""
    operations = 80
    policy = RetryPolicy("bounded", max_attempts=3)
    backend = LocalBackend()

    def operate(number: int) -> tuple[int, bool]:
        budget = policy.budget().consume().consume()
        decision = policy.decide(TimeoutError("offline"), 3, budget)
        owner = f"owner-{number}"
        assert backend.acquire_lock(f"lock-{number}", owner)
        return (
            budget.consumed,
            backend.release_lock(f"lock-{number}", owner) and not decision.retry,
        )

    with ThreadPoolExecutor(max_workers=10) as executor:
        outcomes = list(executor.map(operate, range(operations)))

    assert outcomes == [(2, True)] * operations
    assert backend.acquire_lock("lock-0", "verification")
    assert backend.release_lock("lock-0", "verification")


def test_combined_runtime_isolated_instances_complete_in_threads() -> None:
    """Each local composed request executes every stage exactly once per operation."""
    requests = 32

    def execute(number: int) -> tuple[int, int, dict[str, int]]:
        benchmark = CombinedRuntimeBenchmark()
        result = benchmark.run(iterations=1)
        return number, result.operations, dict(benchmark.stage_counts)

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(execute, range(requests)))

    assert {number for number, _operations, _counts in results} == set(range(requests))
    assert all(operations == 1 for _number, operations, _counts in results)
    assert all(
        counts == {name: 1 for name in counts}
        and set(counts)
        == {"policy", "region", "adaptive", "retry", "runtime", "telemetry", "eventbus"}
        for _number, _operations, counts in results
    )
