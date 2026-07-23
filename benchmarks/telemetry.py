"""Offline local telemetry benchmarks without external exporters or payloads."""

from __future__ import annotations

from benchmarks import BenchmarkReport, BenchmarkResult, BenchmarkRunner
from tkai.telemetry import Metric, TelemetryManager


def _manager(enabled: bool) -> TelemetryManager:
    manager = TelemetryManager()
    if enabled:
        manager.start()
    return manager


def benchmark_metric(enabled: bool = True, iterations: int = 10) -> BenchmarkResult:
    manager = _manager(enabled)
    metric = Metric("benchmark.counter", 1)

    def operation() -> None:
        manager.record(metric)
        manager.metrics.clear()
        local = manager.registry.get("local")
        local.metrics.clear()
        manager.events.clear()

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_trace(iterations: int = 10) -> BenchmarkResult:
    manager = _manager(True)

    def operation() -> None:
        trace = manager.begin_span("benchmark")
        manager.end_span(trace)
        manager.events.clear()

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_structured_log(iterations: int = 10) -> BenchmarkResult:
    manager = _manager(True)

    def operation() -> None:
        manager.log("info", "benchmark", attributes={"operation": "local"})
        manager.logging.records.clear()
        manager.registry.get("local").logs.clear()
        manager.events.clear()

    return BenchmarkRunner(iterations=iterations, random_seed=17).run(operation)


def benchmark_snapshot(iterations: int = 10) -> BenchmarkResult:
    manager = _manager(False)
    return BenchmarkRunner(iterations=iterations, random_seed=17).run(manager.summary)


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    return benchmark_metric(True, iterations)


if __name__ == "__main__":
    BenchmarkReport.emit("telemetry.enabled_metric", run_benchmark())
