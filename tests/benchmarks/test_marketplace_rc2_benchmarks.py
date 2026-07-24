"""Structural Marketplace RC-2 benchmark validation without speed thresholds."""

from benchmarks import BenchmarkReport
from benchmarks.marketplace import MARKETPLACE_BENCHMARKS


def test_marketplace_benchmarks_emit_complete_offline_reports() -> None:
    for name, benchmark in MARKETPLACE_BENCHMARKS:
        result = benchmark(3)
        assert result.operations == 3
        assert result.min_latency_ms >= 0
        assert name in BenchmarkReport.to_markdown(name, result)
        assert f'"module":"{name}"' in BenchmarkReport.to_json(name, result)
