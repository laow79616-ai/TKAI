"""Short, bounded soak smoke coverage; extended mode is explicitly opt-in."""

from __future__ import annotations

import os

from benchmarks.combined_runtime import CombinedRuntimeBenchmark


def test_local_combined_runtime_soak_smoke_stays_bounded() -> None:
    """Repeat local operations without retaining events or unbounded metric history."""
    iterations = 1_000 if os.getenv("TKAI_EXTENDED_SOAK") == "1" else 200
    benchmark = CombinedRuntimeBenchmark()
    result = benchmark.run(iterations=iterations)

    assert result.operations == iterations
    assert all(count == iterations for count in benchmark.stage_counts.values())
    assert benchmark.bus.events == []
    assert benchmark.telemetry.metrics.snapshot() == []
    assert benchmark.telemetry.registry.get("local").metrics == []
