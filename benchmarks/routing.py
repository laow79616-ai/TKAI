"""Offline routing throughput benchmark for the V1.1 RC validation suite."""

from __future__ import annotations

from _runner import BenchmarkResult, render, run

from tkai.routing import ProviderMetadata, RoutingManager


def run_benchmark(
    iterations: tuple[int, ...] = (100, 1_000, 10_000, 100_000),
) -> list[BenchmarkResult]:
    """Measure deterministic routing decisions at the RC target scales."""
    manager = RoutingManager()
    manager.register(ProviderMetadata("local", capabilities=frozenset({"chat"})))
    return [
        run(
            f"routing.{count}",
            lambda: manager.route(required_capabilities=frozenset({"chat"})),
            count,
        )
        for count in iterations
    ]


if __name__ == "__main__":
    print(render(run_benchmark()))
