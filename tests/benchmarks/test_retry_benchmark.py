"""Offline bounded Retry benchmark behavior tests."""

from benchmarks import BenchmarkResult
from benchmarks import retry as suite


def test_retry_scenarios_are_bounded_and_return_results() -> None:
    for result in (
        suite.benchmark_retryable_decision(2),
        suite.benchmark_non_retryable_decision(2),
        suite.benchmark_budget_limit(2),
        suite.benchmark_manager_path(2),
    ):
        assert isinstance(result, BenchmarkResult)
        assert result.operations == 2
        assert result.elapsed_seconds >= 0.0
