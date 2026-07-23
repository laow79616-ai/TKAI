"""V1.3 offline fault, lifecycle, cleanup, and recovery regression validation."""

from __future__ import annotations

from benchmarks.v13_runtime import FakeRedisClient
from tkai.distributed import (
    BackendHealthChecker,
    BackendHealthStatus,
    FailoverConfig,
    FailoverManager,
    LocalMemoryBackend,
    RedisBackend,
)
from tkai.runtime_scheduler import RuntimeScheduler
from tkai.telemetry import LocalExporter, Metric, TelemetryManager


class _FailingExporter(LocalExporter):
    """Local exporter double that verifies telemetry failure isolation."""

    def export_metric(self, metric: Metric) -> None:
        del metric
        raise RuntimeError("offline exporter failure")


class _ToggleRedis(FakeRedisClient):
    """Fake client with a deterministic health failure and later recovery."""

    healthy = False

    def ping(self) -> bool:
        return self.healthy


def test_v13_failover_and_health_recover_after_offline_redis_failure() -> None:
    """Failure thresholds select local fallback without corrupting later recovery."""
    client = _ToggleRedis()
    primary = RedisBackend(client=client)
    manager = FailoverManager(
        primary,
        LocalMemoryBackend(),
        config=FailoverConfig(failure_threshold=1, recovery_threshold=1),
        health_checker=BackendHealthChecker(primary),
    )

    assert manager.evaluate().active_backend == "LocalBackend"
    client.healthy = True
    assert manager.evaluate().state.value == "primary_recovered"
    assert manager.manual_failback().active_backend == "RedisBackend"


def test_v13_cleanup_exporter_isolation_and_scheduler_no_candidate_path() -> None:
    """Optional telemetry failure cannot break local scheduling or cleanup reuse."""
    telemetry = TelemetryManager()
    telemetry.register_exporter("failing", _FailingExporter())
    telemetry.record(Metric("v13.failure", 1), exporter="failing")
    assert len(telemetry.metrics.snapshot()) == 1
    telemetry.metrics.clear()
    assert telemetry.metrics.snapshot() == []

    scheduler = RuntimeScheduler()
    assert scheduler.schedule().provider is None
    checker = BackendHealthChecker(LocalMemoryBackend())
    checker.start()
    checker.stop()
    checker.stop()
    assert checker.snapshot().status in {
        BackendHealthStatus.HEALTHY,
        BackendHealthStatus.DEGRADED,
        BackendHealthStatus.UNHEALTHY,
    }
