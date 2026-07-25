"""Offline EventBus benchmark behavior and subscriber isolation tests."""

from benchmarks import BenchmarkResult
from benchmarks import eventbus as suite


def test_eventbus_scenarios_are_bounded_and_isolate_failures() -> None:
    for result in (
        suite.benchmark_publish(0, 2),
        suite.benchmark_publish(3, 2),
        suite.benchmark_subscribe_cycle(2),
        suite.benchmark_exception_isolation(2),
    ):
        assert isinstance(result, BenchmarkResult)
        assert result.operations == 2
    bus, counter = suite._bus(1, failing=True)
    suite._publish_operation(bus)()
    assert counter == [1]
    assert bus.events == []
