"""Offline static multi-region registration, ranking, and selection benchmarks."""

from __future__ import annotations

from benchmarks import BenchmarkReport, BenchmarkResult, BenchmarkRunner
from tkai.multiregion import MultiRegionManager, Region


def _manager() -> MultiRegionManager:
    manager = MultiRegionManager()
    manager.register_region(Region("alpha", priority=2, latency_estimate_ms=10.0))
    manager.register_region(Region("beta", priority=1, latency_estimate_ms=20.0))
    manager.register_region(Region("gamma", priority=1, latency_estimate_ms=30.0))
    return manager


def benchmark_register(iterations: int = 10) -> BenchmarkResult:
    counter = [0]

    def operation() -> None:
        manager = MultiRegionManager()
        name = f"region-{counter[0]}"
        counter[0] += 1
        manager.register_region(Region(name))
        manager.remove_region(name)

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_rank(iterations: int = 10) -> BenchmarkResult:
    manager = _manager()

    def operation() -> None:
        manager.router.rank(manager.registry.list())
        manager.events.clear()

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_select(iterations: int = 10) -> BenchmarkResult:
    manager = _manager()

    def operation() -> None:
        manager.select_region()
        manager.events.clear()

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_unavailable(iterations: int = 10) -> BenchmarkResult:
    manager = MultiRegionManager()

    def operation() -> None:
        try:
            manager.select_region()
        except Exception:
            return None
        raise AssertionError("empty region registry must not select a region")

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    return benchmark_select(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("multiregion.select", run_benchmark())
