"""Structure-only, offline V1.3 benchmark validation without speed thresholds."""

from __future__ import annotations

from benchmarks import BenchmarkReport
from benchmarks.v13_runtime import (
    benchmark_combined_runtime,
    benchmark_failover,
    benchmark_health,
    benchmark_redis_backend,
    benchmark_registry,
    benchmark_scheduler,
    benchmark_telemetry,
)


def test_v13_benchmark_scenarios_have_complete_stable_reports() -> None:
    """Every V1.3 scenario returns safe statistics and report representations."""
    for name, benchmark in (
        ("redis_backend", benchmark_redis_backend),
        ("health", benchmark_health),
        ("service_registry", benchmark_registry),
        ("telemetry", benchmark_telemetry),
        ("runtime_scheduler", benchmark_scheduler),
        ("failover", benchmark_failover),
        ("combined_runtime", benchmark_combined_runtime),
    ):
        result = benchmark(3)
        assert result.operations == 3
        assert result.min_latency_ms >= 0
        assert name in BenchmarkReport.to_markdown(name, result)
        assert f'"module":"{name}"' in BenchmarkReport.to_json(name, result)
