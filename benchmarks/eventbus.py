"""Offline EventBus publish benchmark at increasing subscriber counts."""

from __future__ import annotations

from _runner import BenchmarkResult, render, run

from tkai.observability import Event, EventBus


def run_benchmark(iterations: int = 10_000) -> list[BenchmarkResult]:
    """Measure dispatch cost for one, ten, and one hundred local subscribers."""
    results: list[BenchmarkResult] = []
    for subscriber_count in (1, 10, 100):
        bus = EventBus()
        handlers = [lambda event: None for _ in range(subscriber_count)]
        for handler in handlers:
            bus.subscribe(handler)
        results.append(
            run(
                f"eventbus.publish.{subscriber_count}",
                lambda bus=bus: bus.publish(Event("Benchmark")),
                iterations,
            )
        )
    return results


if __name__ == "__main__":
    print(render(run_benchmark()))
