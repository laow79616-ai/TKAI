"""Offline telemetry enabled and disabled benchmark behavior tests."""

from benchmarks import BenchmarkResult
from benchmarks import telemetry as suite


def test_telemetry_scenarios_are_local_and_safe() -> None:
    for result in (
        suite.benchmark_metric(True, 2),
        suite.benchmark_metric(False, 2),
        suite.benchmark_trace(2),
        suite.benchmark_structured_log(2),
        suite.benchmark_snapshot(2),
    ):
        assert isinstance(result, BenchmarkResult)
        assert result.operations == 2
        assert result.max_latency_ms >= 0.0
