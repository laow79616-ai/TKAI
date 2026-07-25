"""Stable human and machine benchmark report rendering checks."""

import json

from benchmarks import BenchmarkReport, BenchmarkResult


def test_markdown_report_contains_all_comparison_fields() -> None:
    result = BenchmarkResult(operations=3, elapsed_seconds=1.5, ops_per_second=2.0)
    report = BenchmarkReport.to_markdown("routing", result)
    for field in (
        "Module",
        "Operations",
        "Elapsed",
        "Ops/sec",
        "Mean",
        "P50",
        "P95",
        "P99",
        "Min",
        "Max",
    ):
        assert field in report
    assert "routing" in report


def test_json_report_is_stable_and_serializable() -> None:
    result = BenchmarkResult(operations=1)
    report = BenchmarkReport.to_json("cache", result)
    assert json.loads(report) == {"module": "cache", "result": result.to_dict()}
