"""Offline benchmarks for LocalBackend, membership, and LocalLock operations."""

from __future__ import annotations

from datetime import datetime, timezone

from benchmarks import BenchmarkReport, BenchmarkResult, BenchmarkRunner
from tkai.distributed import DistributedCoordinator, LocalBackend, Node


def benchmark_backend(iterations: int = 10) -> BenchmarkResult:
    backend = LocalBackend()
    backend.connect()

    def operation() -> None:
        backend.set("benchmark", "value")
        backend.get("benchmark")
        backend.delete("benchmark")

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_lock(iterations: int = 10) -> BenchmarkResult:
    now = datetime.now(timezone.utc)
    coordinator = DistributedCoordinator(Node("benchmark", "local", now, now))
    coordinator.start()
    lock = coordinator.lock("benchmark")

    def operation() -> None:
        assert lock.acquire()
        assert lock.release()

    result = BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)
    coordinator.stop()
    return result


def benchmark_membership_snapshot(iterations: int = 10) -> BenchmarkResult:
    now = datetime.now(timezone.utc)
    coordinator = DistributedCoordinator(Node("benchmark", "local", now, now))
    coordinator.start()
    result = BenchmarkRunner(iterations=iterations, random_seed=17).run(
        coordinator.membership.snapshot
    )
    coordinator.stop()
    return result


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    return benchmark_backend(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("distributed.local_backend", run_benchmark())
