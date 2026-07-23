"""Offline V1.3 RC-1 integration and compatibility regression coverage."""

from __future__ import annotations

import importlib
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from typer.testing import CliRunner

from tkai.ai import DoctorService
from tkai.commands import ai as ai_commands
from tkai.configuration import ConfigurationManager, ConfigurationResolver
from tkai.configuration.sources.memory import MemoryConfigurationLoader
from tkai.distributed import (
    BackendConfig,
    BackendFactory,
    BackendHealthStatus,
    DistributedCoordinator,
    LocalMemoryBackend,
    Node,
    RedisBackend,
)
from tkai.observability import EventBus
from tkai.policy import PolicyContext, PolicyManager, PolicyStage
from tkai.retry import RetryManager, RetryPolicy
from tkai.runtime_scheduler import RuntimeScheduler, SchedulingPolicy
from tkai.telemetry import Metric, TelemetryManager


class _FakeRedisClient:
    """Minimal offline client for Redis construction and active health checks."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    def ping(self) -> bool:
        return True

    def get(self, key: str) -> bytes | None:
        value = self.values.get(key)
        return value.encode("utf-8") if value is not None else None

    def set(
        self, key: str, value: str, *, nx: bool = False, ex: int | None = None
    ) -> bool:
        del ex
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def delete(self, key: str) -> int:
        return int(self.values.pop(key, None) is not None)

    def publish(self, topic: str, value: str) -> int:
        del topic, value
        return 0

    def close(self) -> None:
        return None


def test_v13_optional_components_share_an_explicit_offline_lifecycle() -> None:
    """Exercise backend, health, failover, telemetry, scheduler, and services."""
    bus = EventBus()
    redis = RedisBackend(client=_FakeRedisClient())
    checker = BackendFactory.create_health_checker(
        redis, BackendConfig(health_probe_retries=0)
    )
    failover = BackendFactory.create_failover_manager(redis, LocalMemoryBackend())
    registry = BackendFactory.create_service_registry(backend=redis)
    telemetry = BackendFactory.create_telemetry_manager()
    telemetry.event_bus = bus
    policies = PolicyManager(event_bus=bus)
    retries = RetryManager(event_bus=bus)
    retries.register(RetryPolicy("local"))
    now = datetime.now(timezone.utc)
    coordinator = DistributedCoordinator(Node("rc1", "local", now, now), event_bus=bus)
    scheduler = RuntimeScheduler(telemetry=telemetry)
    scheduler.register("primary", latency_ms=5, cost=1)

    telemetry.start()
    coordinator.start()
    checker.start()
    checker.stop()
    assert checker.probe().status is BackendHealthStatus.HEALTHY
    assert failover.evaluate().active_backend == "RedisBackend"
    assert registry.list() == ()
    telemetry.record(Metric("rc1.integration", 1))
    assert scheduler.schedule(SchedulingPolicy.ADAPTIVE).provider == "primary"
    assert retries.run(lambda: "ok", policy="local") == "ok"
    assert policies.execute(PolicyContext(PolicyStage.BEFORE_REQUEST)) == ()

    coordinator.stop()
    coordinator.stop()
    telemetry.stop()
    telemetry.stop()
    failover.stop()
    registry.stop()


def test_v13_public_imports_and_configuration_overrides_remain_additive() -> None:
    """Keep V1.2 imports and established configuration precedence available."""
    for name in (
        "tkai.ai",
        "tkai.distributed",
        "tkai.telemetry",
        "tkai.policy",
        "tkai.retry",
        "tkai.runtime_scheduler",
    ):
        assert importlib.import_module(name) is not None

    defaults = ConfigurationManager(ConfigurationResolver([])).load()
    legacy = ConfigurationManager(
        ConfigurationResolver([MemoryConfigurationLoader({"provider": {"timeout": 5}})])
    ).load()
    explicit = ConfigurationManager(
        ConfigurationResolver(
            [
                MemoryConfigurationLoader({"provider": {"timeout": 5}}),
                MemoryConfigurationLoader({"provider": {"timeout": 10}}),
            ]
        )
    ).load()
    assert defaults.source == "default"
    assert legacy.get("provider.timeout") == 5
    assert explicit.get("provider.timeout") == 10


def test_v13_concurrent_scheduler_health_and_backend_operations_are_isolated() -> None:
    """Validate deterministic local concurrency without threads owned after return."""
    backend = LocalMemoryBackend()
    backend.connect()
    checker = BackendFactory.create_health_checker(backend)
    scheduler = RuntimeScheduler()
    scheduler.register("one", latency_ms=1)
    scheduler.register("two", latency_ms=2)

    with ThreadPoolExecutor(max_workers=8) as executor:
        decisions = list(executor.map(lambda _: scheduler.schedule(), range(24)))
        snapshots = list(executor.map(lambda _: checker.probe(), range(24)))
        list(executor.map(lambda value: backend.set(str(value), value), range(24)))

    assert all(item.provider in {"one", "two"} for item in decisions)
    assert all(item.status is BackendHealthStatus.HEALTHY for item in snapshots)
    assert all(backend.get(str(value)) == value for value in range(24))
    backend.disconnect()


def test_v13_subscriber_failure_isolated_from_doctor_and_cli_smoke() -> None:
    """A failing observer must not block diagnostics or established AI commands."""
    bus = EventBus()
    bus.subscribe(lambda _event: (_ for _ in ()).throw(RuntimeError("observer")))
    telemetry = TelemetryManager(event_bus=bus)
    telemetry.start()
    telemetry.record(Metric("rc1.observer", 1))
    report = DoctorService(telemetry=telemetry).run()

    runner = CliRunner()
    assert runner.invoke(ai_commands.app, ["--help"]).exit_code == 0
    assert runner.invoke(ai_commands.app, ["doctor", "--json"]).exit_code == 0
    assert telemetry.summary()["metrics"] == 1
    assert report.to_json()
    telemetry.stop()
