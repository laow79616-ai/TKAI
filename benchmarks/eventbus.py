"""Offline EventBus benchmarks with bounded event history and safe subscribers."""

from __future__ import annotations

from collections.abc import Callable

from benchmarks import BenchmarkReport, BenchmarkResult, BenchmarkRunner
from tkai.observability import Event, EventBus


def _bus(subscribers: int, *, failing: bool = False) -> tuple[EventBus, list[int]]:
    bus = EventBus()
    counter = [0]

    def count_handler() -> Callable[[Event], None]:
        def count(_event: Event) -> None:
            counter[0] += 1

        return count

    def fail(_event: Event) -> None:
        raise RuntimeError("local")

    for _ in range(subscribers):
        bus.subscribe(count_handler())
    if failing:
        bus.subscribe(fail)
    return bus, counter


def _publish_operation(bus: EventBus) -> Callable[[], None]:
    event = Event("Benchmark")

    def operation() -> None:
        bus.publish(event)
        bus.events.clear()

    return operation


def benchmark_publish(subscribers: int = 0, iterations: int = 10) -> BenchmarkResult:
    bus, _counter = _bus(subscribers)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        _publish_operation(bus)
    )


def benchmark_subscribe_cycle(iterations: int = 10) -> BenchmarkResult:
    bus = EventBus()

    def handler(_event: Event) -> None:
        return None

    def operation() -> None:
        bus.subscribe(handler)
        bus.unsubscribe(handler)

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_exception_isolation(iterations: int = 10) -> BenchmarkResult:
    bus, _counter = _bus(1, failing=True)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        _publish_operation(bus)
    )


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    return benchmark_publish(1, iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("eventbus.single_subscriber", run_benchmark())
