"""Offline tests for benchmark infrastructure; never run benchmark workloads."""

# ruff: noqa: E402

from pathlib import Path

__path__.append(str(Path(__file__).resolve().parents[2] / "benchmarks"))

from .base import BenchmarkRunner
from .models import BenchmarkResult
from .report import BenchmarkReport
from .statistics import LatencyStatistics, calculate_statistics, percentile
from .timer import HighResolutionTimer, TimerStateError

__all__ = (
    "BenchmarkReport",
    "BenchmarkResult",
    "BenchmarkRunner",
    "HighResolutionTimer",
    "LatencyStatistics",
    "TimerStateError",
    "calculate_statistics",
    "percentile",
)
