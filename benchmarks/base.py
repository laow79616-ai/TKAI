"""Repeatable, offline benchmark runner independent of TKAI runtime behavior."""

from __future__ import annotations

import random
from collections.abc import Callable

from .models import BenchmarkResult
from .statistics import calculate_statistics
from .timer import HighResolutionTimer


class BenchmarkRunner:
    """Run a local callable with optional warmup, repetition, and fixed seeding."""

    def __init__(
        self,
        *,
        warmup: int = 0,
        iterations: int = 1,
        repeats: int = 1,
        random_seed: int | None = None,
    ) -> None:
        if min(warmup, iterations, repeats) < 0:
            raise ValueError("warmup, iterations, and repeats must not be negative")
        self.warmup = warmup
        self.iterations = iterations
        self.repeats = repeats
        self.random_seed = random_seed

    def run(self, operation: Callable[[], object]) -> BenchmarkResult:
        """Measure operation latency in milliseconds without any network activity."""
        original_random_state = random.getstate()
        latencies_ns: list[int] = []
        try:
            for repeat in range(self.repeats):
                if self.random_seed is not None:
                    random.seed(self.random_seed + repeat)
                for _ in range(self.warmup):
                    operation()
                for _ in range(self.iterations):
                    timer = HighResolutionTimer().start()
                    operation()
                    latencies_ns.append(timer.stop())
        finally:
            random.setstate(original_random_state)
        if not latencies_ns:
            return BenchmarkResult()
        elapsed_seconds = sum(latencies_ns) / 1_000_000_000
        latencies_ms = [latency / 1_000_000 for latency in latencies_ns]
        statistics = calculate_statistics(latencies_ms)
        operations = len(latencies_ns)
        return BenchmarkResult(
            operations=operations,
            elapsed_seconds=elapsed_seconds,
            ops_per_second=operations / elapsed_seconds if elapsed_seconds else 0.0,
            mean_latency_ms=statistics.mean_ms,
            p50_latency_ms=statistics.p50_ms,
            p95_latency_ms=statistics.p95_ms,
            p99_latency_ms=statistics.p99_ms,
            min_latency_ms=statistics.min_ms,
            max_latency_ms=statistics.max_ms,
        )
