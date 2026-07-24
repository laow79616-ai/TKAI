"""Structural Studio RC-2 benchmark coverage without machine-speed thresholds."""

from __future__ import annotations

from benchmarks import BenchmarkReport
from benchmarks.studio import STUDIO_BENCHMARKS


def test_studio_benchmarks_have_complete_offline_reports() -> None:
    """Every Studio scenario is bounded and can render Markdown and JSON."""
    for name, benchmark in STUDIO_BENCHMARKS:
        result = benchmark(3)
        assert result.operations == 3
        assert result.min_latency_ms >= 0
        assert name in BenchmarkReport.to_markdown(name, result)
        assert f'"module":"{name}"' in BenchmarkReport.to_json(name, result)
