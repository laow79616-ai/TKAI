"""Tests for deterministic non-mutating benchmark latency statistics."""

from benchmarks.statistics import calculate_statistics, percentile


def test_percentiles_are_safe_for_empty_and_single_values() -> None:
    assert percentile([], 50) == 0.0
    assert percentile([3.0], 50) == 3.0
    assert calculate_statistics([]).mean_ms == 0.0


def test_nearest_rank_percentiles_are_stable_without_input_mutation() -> None:
    values = [8.0, 1.0, 7.0, 2.0, 6.0, 3.0, 5.0, 4.0]
    original = list(values)
    assert percentile(values, 50) == 4.0
    assert percentile(values, 95) == 8.0
    assert percentile(values, 99) == 8.0
    assert values == original


def test_large_sample_statistics_are_deterministic() -> None:
    values = [float(value) for value in range(1, 1001)]
    statistics = calculate_statistics(values)
    assert statistics.mean_ms == 500.5
    assert statistics.p50_ms == 500.0
    assert statistics.p95_ms == 950.0
    assert statistics.p99_ms == 990.0
    assert statistics.min_ms == 1.0
    assert statistics.max_ms == 1000.0
