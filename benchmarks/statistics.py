"""Deterministic latency statistics using a documented nearest-rank percentile."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from math import ceil
from statistics import fmean


@dataclass(frozen=True, slots=True)
class LatencyStatistics:
    """Immutable summary of latency values represented in milliseconds."""

    mean_ms: float = 0.0
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0


def percentile(values: Sequence[float], percentage: float) -> float:
    """Return a nearest-rank percentile without mutating ``values``.

    Values are copied and sorted. For ``n`` values, rank is
    ``ceil(percentage / 100 * n)`` and the returned zero-based index is
    ``max(0, rank - 1)``. Empty input returns ``0.0`` to keep empty benchmarks
    safe and comparable.
    """
    if not 0.0 <= percentage <= 100.0:
        raise ValueError("percentage must be between zero and one hundred")
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, ceil(percentage / 100.0 * len(ordered)) - 1)
    return float(ordered[index])


def calculate_statistics(values: Sequence[float]) -> LatencyStatistics:
    """Calculate stable statistics, returning zeroes for an empty sequence."""
    if not values:
        return LatencyStatistics()
    ordered = sorted(values)
    return LatencyStatistics(
        mean_ms=float(fmean(ordered)),
        p50_ms=percentile(ordered, 50.0),
        p95_ms=percentile(ordered, 95.0),
        p99_ms=percentile(ordered, 99.0),
        min_ms=float(ordered[0]),
        max_ms=float(ordered[-1]),
    )
