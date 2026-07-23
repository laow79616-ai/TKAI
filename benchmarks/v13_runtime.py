"""Offline, bounded benchmark scenarios for explicit V1.3 runtime components."""

from __future__ import annotations

from datetime import datetime, timezone

from benchmarks import BenchmarkReport, BenchmarkResult, BenchmarkRunner
from tkai.distributed import (
    BackendFactory,
    BackendHealthStatus,
    FailoverManager,
    LocalMemoryBackend,
    LocalServiceRegistry,
    RedisBackend,
    ServiceInstance,
)
from tkai.runtime_scheduler import RuntimeScheduler, SchedulingPolicy
from tkai.telemetry import Metric, TelemetryManager


class FakeRedisClient:
    """Small injected client so every Redis benchmark remains offline."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> bytes | None:
        value = self.values.get(key)
        return value.encode() if value is not None else None

    def set(
        self,
        key: str,
        value: str,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        del ex
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def delete(self, key: str) -> int:
        return int(self.values.pop(key, None) is not None)

    def publish(self, topic: str, value: str) -> int:
        del topic, value
        return 0

    def close(self) -> None:
        return None


def benchmark_redis_backend(iterations: int = 10) -> BenchmarkResult:
    """Measure injected-client set/get/delete and JSON-safe backend handling."""
    backend = RedisBackend(client=FakeRedisClient())

    def operation() -> None:
        backend.set("benchmark", {"offline": True})
        assert backend.get("benchmark") == {"offline": True}
        assert backend.delete("benchmark")

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_health(iterations: int = 10) -> BenchmarkResult:
    """Measure cached health snapshot reads after one explicit local probe."""
    backend = LocalMemoryBackend()
    backend.connect()
    checker = BackendFactory.create_health_checker(backend)
    assert checker.probe().status is BackendHealthStatus.HEALTHY
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(checker.snapshot)


def benchmark_registry(iterations: int = 10) -> BenchmarkResult:
    """Measure deterministic local registration, lookup, and cleanup work."""
    registry = LocalServiceRegistry()
    now = datetime.now(timezone.utc)
    instance = ServiceInstance.create("api", "benchmark", "local://api", now=now)

    def operation() -> None:
        registry.register(instance)
        assert registry.lookup("api") == (instance,)
        assert registry.deregister("api", "benchmark")

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_telemetry(iterations: int = 10) -> BenchmarkResult:
    """Measure local metric and structured-log recording without external export."""
    telemetry = TelemetryManager()
    telemetry.start()

    def operation() -> None:
        telemetry.record(Metric("v13.benchmark", 1))
        telemetry.log("info", "offline")
        telemetry.metrics.clear()
        telemetry.logging.records.clear()
        telemetry.events.clear()

    result = BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)
    telemetry.stop()
    return result


def benchmark_scheduler(iterations: int = 10) -> BenchmarkResult:
    """Measure explicit deterministic adaptive scheduler decisions."""
    scheduler = RuntimeScheduler()
    scheduler.register("fast", latency_ms=1, cost=2, weight=2)
    scheduler.register("cheap", latency_ms=2, cost=1)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(
        lambda: scheduler.schedule(SchedulingPolicy.ADAPTIVE)
    )


def benchmark_failover(iterations: int = 10) -> BenchmarkResult:
    """Measure explicit healthy-primary snapshots and evaluation transitions."""
    primary = LocalMemoryBackend()
    primary.connect()
    manager = FailoverManager(primary)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(manager.evaluate)


def benchmark_combined_runtime(iterations: int = 10) -> BenchmarkResult:
    """Measure one local registry-to-health-to-scheduler telemetry composition."""
    backend = LocalMemoryBackend()
    backend.connect()
    checker = BackendFactory.create_health_checker(backend)
    failover = FailoverManager(backend)
    registry = LocalServiceRegistry()
    now = datetime.now(timezone.utc)
    instance = ServiceInstance.create("api", "local", "local://api", now=now)
    registry.register(instance)
    telemetry = TelemetryManager()
    telemetry.start()
    scheduler = RuntimeScheduler(telemetry=telemetry)
    scheduler.register("local", latency_ms=1)

    def operation() -> None:
        assert registry.lookup("api") == (instance,)
        assert checker.probe().status is BackendHealthStatus.HEALTHY
        assert failover.snapshot().active_backend == "LocalBackend"
        assert scheduler.schedule().provider == "local"
        telemetry.record(Metric("v13.combined", 1))
        telemetry.metrics.clear()
        telemetry.events.clear()

    result = BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)
    telemetry.stop()
    return result


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    """Retain the standard module entry point using the combined scheduler path."""
    return benchmark_scheduler(iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("v13.runtime_scheduler", run_benchmark())
