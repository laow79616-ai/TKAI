"""Accelerated release validation for local Marketplace Server foundations."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

from benchmarks.server import SERVER_BENCHMARKS, reports
from server.health import (
    HealthCheck,
    HealthCheckId,
    HealthResult,
    HealthStatus,
    ReferenceHealthService,
)
from server.statistics import (
    ReferenceStatisticsService,
    StatisticsMetric,
    StatisticsMetricType,
    StatisticsRecord,
    StatisticsSource,
    StatisticsSourceType,
    StatisticsValue,
)

ROOT = Path(__file__).resolve().parents[3]


def _workflow() -> tuple[int, int, bool]:
    statistics = ReferenceStatisticsService()
    statistics.register_source(
        StatisticsSource("server", StatisticsSourceType.CUSTOM, "server")
    )
    statistics.record(
        StatisticsRecord(
            "record",
            "server",
            StatisticsMetric("items", StatisticsMetricType.COUNTER),
            StatisticsValue(1),
        )
    )
    health = ReferenceHealthService()
    health.register_check(HealthCheck("server"))
    health.update_result(HealthResult(HealthCheckId("server"), HealthStatus.HEALTHY))
    snapshot = statistics.snapshot()
    health.close()
    return (
        snapshot.counters.total_records,
        health.statistics().healthy,
        health.snapshot().closed,
    )


def test_reference_workflow_and_ten_reliability_rounds_are_stable() -> None:
    assert tuple(_workflow() for _ in range(10)) == ((1, 1, True),) * 10


def test_server_benchmarks_are_offline_complete_and_threshold_free() -> None:
    rendered = reports(3)
    assert len(rendered) == len(SERVER_BENCHMARKS)
    for name, benchmark in SERVER_BENCHMARKS:
        result = benchmark(3)
        assert result.operations == 3 and result.min_latency_ms >= 0
        assert name in rendered and name in rendered[name]["markdown"]
        assert json.loads(rendered[name]["json"])["module"] == name


def test_public_imports_and_server_release_docs_are_packaged() -> None:
    for module in (
        "server.registry",
        "server.publisher",
        "server.package",
        "server.version",
        "server.search",
        "server.statistics",
        "server.health",
    ):
        assert importlib.import_module(module)
    manifest = (ROOT / "MANIFEST.in").read_text(encoding="utf-8")
    config = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for document in (
        "AcceleratedReleaseValidation.md",
        "ReleaseNotes.md",
        "RC1IntegrationValidation.md",
    ):
        assert document in manifest and document in config
