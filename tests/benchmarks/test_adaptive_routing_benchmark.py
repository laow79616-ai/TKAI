"""Offline deterministic Adaptive Routing benchmark behavior tests."""

from benchmarks import BenchmarkResult
from benchmarks import adaptive_routing as suite


def test_adaptive_ranking_and_cold_start_are_stable() -> None:
    for result in (
        suite.benchmark_signal_record(2),
        suite.benchmark_rank(2),
        suite.benchmark_cold_start(2),
    ):
        assert isinstance(result, BenchmarkResult)
        assert result.operations == 2
    manager = suite._manager()
    first = [score.provider for score in manager.rank_providers(suite._PROVIDERS)]
    second = [score.provider for score in manager.rank_providers(suite._PROVIDERS)]
    assert first == second
