"""Offline LocalBackend and LocalLock benchmark behavior tests."""

from benchmarks import BenchmarkResult
from benchmarks import distributed as suite


def test_distributed_benchmarks_clean_up_local_resources() -> None:
    for result in (
        suite.benchmark_backend(2),
        suite.benchmark_lock(2),
        suite.benchmark_membership_snapshot(2),
    ):
        assert isinstance(result, BenchmarkResult)
        assert result.operations == 2
        assert result.ops_per_second >= 0.0
