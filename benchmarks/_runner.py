"""Small dependency-free, offline benchmark runner used by RC validation."""

from __future__ import annotations

import json
import statistics
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    """Stable timing result emitted by every RC benchmark."""

    name: str
    iterations: int
    ops_per_second: float
    average_latency_ms: float
    median_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    max_latency_ms: float
    cpu_time_ms: float
    wall_time_ms: float

    def to_dict(self) -> dict[str, float | int | str]:
        """Return a JSON-ready result with deterministic field names."""
        return asdict(self)


def run(name: str, operation: Callable[[], Any], iterations: int) -> BenchmarkResult:
    """Measure a local synchronous operation without network or warm-up I/O."""
    if iterations < 1:
        raise ValueError("iterations must be positive")
    samples: list[int] = []
    cpu_start = time.process_time_ns()
    wall_start = time.perf_counter_ns()
    for _ in range(iterations):
        start = time.perf_counter_ns()
        operation()
        samples.append(time.perf_counter_ns() - start)
    wall_elapsed = time.perf_counter_ns() - wall_start
    cpu_elapsed = time.process_time_ns() - cpu_start
    return _result(name, iterations, samples, wall_elapsed, cpu_elapsed)


def _result(
    name: str,
    iterations: int,
    samples: Sequence[int],
    wall_elapsed: int,
    cpu_elapsed: int,
) -> BenchmarkResult:
    """Turn nanosecond samples into a compact, consistent result."""
    milliseconds = sorted(sample / 1_000_000 for sample in samples)
    wall_seconds = wall_elapsed / 1_000_000_000
    return BenchmarkResult(
        name=name,
        iterations=iterations,
        ops_per_second=iterations / wall_seconds if wall_seconds else float("inf"),
        average_latency_ms=statistics.fmean(milliseconds),
        median_latency_ms=statistics.median(milliseconds),
        p95_latency_ms=_percentile(milliseconds, 0.95),
        p99_latency_ms=_percentile(milliseconds, 0.99),
        max_latency_ms=milliseconds[-1],
        cpu_time_ms=cpu_elapsed / 1_000_000,
        wall_time_ms=wall_elapsed / 1_000_000,
    )


def _percentile(samples: Sequence[float], percentile: float) -> float:
    """Return a deterministic nearest-rank percentile for non-empty samples."""
    index = max(0, min(len(samples) - 1, int(len(samples) * percentile + 0.5) - 1))
    return samples[index]


def render(results: Sequence[BenchmarkResult]) -> str:
    """Serialize a benchmark suite as stable, human and machine-readable JSON."""
    return json.dumps(
        [result.to_dict() for result in results], indent=2, sort_keys=True
    )
