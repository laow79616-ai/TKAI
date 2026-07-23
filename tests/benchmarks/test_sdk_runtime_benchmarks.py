"""Structural reports for offline TKAI 2.0 SDK benchmark scenarios."""

from __future__ import annotations

from benchmarks import BenchmarkReport
from benchmarks.sdk_runtime import SDK_BENCHMARKS


def test_sdk_benchmarks_return_complete_markdown_and_json_reports() -> None:
    """Every SDK scenario has bounded work and stable report representations."""
    for name, benchmark in SDK_BENCHMARKS:
        result = benchmark(3)
        assert result.operations == 3
        assert result.min_latency_ms >= 0
        assert name in BenchmarkReport.to_markdown(name, result)
        assert f'"module":"{name}"' in BenchmarkReport.to_json(name, result)
