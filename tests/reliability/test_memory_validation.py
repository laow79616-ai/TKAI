"""Structural memory validation without allocator-specific thresholds."""

from __future__ import annotations

import gc
import tracemalloc
import weakref
from datetime import datetime, timezone

from benchmarks.combined_runtime import CombinedRuntimeBenchmark
from tkai.adaptive import ProviderHistory, ProviderSignal
from tkai.distributed import LocalBackend
from tkai.observability import Event, EventBus


def test_bounded_histories_and_event_bus_cleanup_do_not_accumulate() -> None:
    """Keep local history bounded and discard event/handler references explicitly."""
    history = ProviderHistory(max_samples_per_provider=8)
    bus = EventBus()
    received: list[str] = []

    def handler(event: Event) -> None:
        received.append(event.name)

    bus.subscribe(handler)
    for number in range(40):
        history.record(
            ProviderSignal("local", datetime.now(timezone.utc), latency_ms=number)
        )
        bus.publish(Event("bounded"))

    assert len(history.snapshot("local")) == 8
    assert len(bus.events) == len(received) == 40
    bus.clear()
    history.clear()
    bus.publish(Event("after-clear"))
    assert [event.name for event in bus.events] == ["after-clear"]
    assert received == ["bounded"] * 40
    assert history.snapshot() == ()


def test_tracemalloc_runs_are_bounded_and_local_objects_are_collectable() -> None:
    """Use tracemalloc for a local bounded run without allocator-size assertions."""
    tracemalloc.start()
    try:
        baseline = tracemalloc.take_snapshot()
        benchmark = CombinedRuntimeBenchmark()
        result = benchmark.run(iterations=30)
        current = tracemalloc.take_snapshot()
        differences = current.compare_to(baseline, "filename")

        assert result.operations == 30
        assert all(count == 30 for count in benchmark.stage_counts.values())
        assert benchmark.bus.events == []
        assert benchmark.telemetry.metrics.snapshot() == []
        assert differences
    finally:
        tracemalloc.stop()

    backend = LocalBackend()
    reference = weakref.ref(backend)
    backend.set("local", object())
    assert backend.delete("local")
    del backend
    gc.collect()
    assert reference() is None
