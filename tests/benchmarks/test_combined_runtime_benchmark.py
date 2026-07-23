"""Pure local combined-runtime benchmark path tests."""

from benchmarks import BenchmarkResult
from benchmarks.combined_runtime import CombinedRuntimeBenchmark


def test_combined_runtime_counts_each_stage_once_and_stays_local() -> None:
    benchmark = CombinedRuntimeBenchmark()
    result = benchmark.run(2)
    assert isinstance(result, BenchmarkResult)
    assert result.operations == 2
    expected = {
        "policy",
        "region",
        "adaptive",
        "retry",
        "runtime",
        "telemetry",
        "eventbus",
    }
    assert set(benchmark.stage_counts) == expected
    assert all(count == 2 for count in benchmark.stage_counts.values())
    assert result.elapsed_seconds * 1_000_000_000 >= sum(
        benchmark.stage_elapsed_ns.values()
    )
    assert benchmark.telemetry.summary()["metrics"] == 0
    assert benchmark.bus.events == []
