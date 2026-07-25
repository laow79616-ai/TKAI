"""Offline Policy benchmark behavior tests."""

from benchmarks import BenchmarkReport, BenchmarkResult
from benchmarks import policy as suite


def test_policy_scenarios_return_results_and_reports() -> None:
    for result in (
        suite.benchmark_allowed(2),
        suite.benchmark_rejected(2),
        suite.benchmark_default(2),
    ):
        assert isinstance(result, BenchmarkResult)
        assert result.operations == 2
        assert result.min_latency_ms >= 0.0
    assert "policy.allowed" in BenchmarkReport.to_markdown(
        "policy.allowed", suite.run_benchmark(1)
    )
