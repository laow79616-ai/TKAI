"""Structural Cloud RC-2 benchmark validation without speed thresholds."""

from benchmarks import BenchmarkReport
from benchmarks.cloud import CLOUD_BENCHMARKS


def test_cloud_benchmarks_emit_complete_offline_reports() -> None:
    """Every Cloud foundation benchmark is bounded and serializable."""
    for name, benchmark in CLOUD_BENCHMARKS:
        result = benchmark(3)
        assert result.operations == 3
        assert result.min_latency_ms >= 0
        assert name in BenchmarkReport.to_markdown(name, result)
        assert f'"module":"{name}"' in BenchmarkReport.to_json(name, result)
