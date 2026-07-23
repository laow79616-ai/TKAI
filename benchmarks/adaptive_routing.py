"""Offline deterministic adaptive-routing history, score, and ranking benchmarks."""

from __future__ import annotations

from datetime import datetime, timezone

from benchmarks import BenchmarkReport, BenchmarkResult, BenchmarkRunner
from tkai.adaptive import AdaptiveRoutingManager, ProviderSignal

_PROVIDERS = ("alpha", "beta", "gamma")


def _manager() -> AdaptiveRoutingManager:
    manager = AdaptiveRoutingManager()
    timestamp = datetime.now(timezone.utc)
    for index, provider in enumerate(_PROVIDERS):
        manager.record_signal(
            ProviderSignal(provider, timestamp, latency_ms=10.0 + index, cost=0.1)
        )
    return manager


def benchmark_signal_record(iterations: int = 10) -> BenchmarkResult:
    manager = AdaptiveRoutingManager()
    signal = ProviderSignal("alpha", datetime.now(timezone.utc), latency_ms=10.0)

    def operation() -> None:
        manager.record_signal(signal)
        manager.history.clear()

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_rank(iterations: int = 10) -> BenchmarkResult:
    manager = _manager()

    def operation() -> None:
        manager.rank_providers(_PROVIDERS)
        manager.events.clear()

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_cold_start(iterations: int = 10) -> BenchmarkResult:
    manager = AdaptiveRoutingManager()

    def operation() -> None:
        manager.rank_providers(_PROVIDERS)
        manager.events.clear()

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    return benchmark_rank(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("adaptive_routing.rank", run_benchmark())
