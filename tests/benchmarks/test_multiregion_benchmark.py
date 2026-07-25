"""Offline static Multi-region benchmark behavior tests."""

from benchmarks import BenchmarkResult
from benchmarks import multiregion as suite


def test_multiregion_ranking_selection_and_unavailable_paths_are_stable() -> None:
    for result in (
        suite.benchmark_register(2),
        suite.benchmark_rank(2),
        suite.benchmark_select(2),
        suite.benchmark_unavailable(2),
    ):
        assert isinstance(result, BenchmarkResult)
        assert result.operations == 2
    manager = suite._manager()
    assert [
        region.region_id for region in manager.router.rank(manager.registry.list())
    ] == [
        "alpha",
        "beta",
        "gamma",
    ]
