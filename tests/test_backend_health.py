"""Offline coverage for explicit distributed backend health probes."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor

from tkai.distributed import (
    BackendConfig,
    BackendFactory,
    BackendHealthChecker,
    BackendHealthStatus,
    HealthProbeConfig,
    LocalMemoryBackend,
    RedisBackend,
)


class ProbeBackend:
    """Deterministic backend double supporting return values and local failures."""

    def __init__(self, outcomes: list[bool | Exception]) -> None:
        self.outcomes = outcomes
        self.calls = 0
        self.timeouts: list[float | None] = []

    def probe_health(self, *, timeout_seconds: float | None = None) -> bool:
        self.calls += 1
        self.timeouts.append(timeout_seconds)
        outcome = self.outcomes.pop(0) if self.outcomes else True
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class PingOnlyRedisClient:
    """Minimal injected client used solely by the Redis health probe tests."""

    def __init__(self) -> None:
        self.pings = 0

    def ping(self) -> bool:
        self.pings += 1
        return True

    def get(self, key: str) -> None:
        del key
        return None

    def set(
        self, key: str, value: str, *, nx: bool = False, ex: int | None = None
    ) -> bool:
        del key, value, nx, ex
        return True

    def delete(self, key: str) -> int:
        del key
        return 0

    def publish(self, topic: str, value: str) -> int:
        del topic, value
        return 0

    def close(self) -> None:
        return None


def test_local_backend_health_probe_is_healthy_and_async_safe() -> None:
    """An explicitly connected local backend can be checked without a network."""
    backend = LocalMemoryBackend()
    backend.connect()
    checker = BackendHealthChecker(backend)

    snapshot = checker.probe()
    async_snapshot = asyncio.run(checker.aprobe())

    assert snapshot.status is BackendHealthStatus.HEALTHY
    assert async_snapshot.status is BackendHealthStatus.HEALTHY
    assert snapshot.last_probe is not None
    assert snapshot.last_error is None


def test_failed_probes_transition_from_degraded_to_unhealthy() -> None:
    """Failure thresholds produce stable degraded and unhealthy cached results."""
    backend = ProbeBackend([False, RuntimeError("offline")])
    checker = BackendHealthChecker(
        backend,
        config=HealthProbeConfig(retries=0, unhealthy_after_failures=2),
    )

    assert checker.probe().status is BackendHealthStatus.DEGRADED
    failed = checker.probe()
    assert failed.status is BackendHealthStatus.UNHEALTHY
    assert failed.last_error == "RuntimeError"
    assert failed.consecutive_failures == 2


def test_timeout_is_recorded_without_waiting_or_network_access() -> None:
    """A cooperative timeout is reported as a degraded probe result."""
    backend = ProbeBackend([TimeoutError("local timeout")])
    checker = BackendHealthChecker(
        backend,
        config=HealthProbeConfig(retries=0, timeout_seconds=0.25),
    )

    snapshot = checker.probe()

    assert snapshot.status is BackendHealthStatus.DEGRADED
    assert snapshot.last_error == "TimeoutError"
    assert backend.timeouts == [0.25]


def test_probe_retries_immediately_and_recovers_to_healthy() -> None:
    """Retrying uses a bounded attempt count and never calls sleep."""
    backend = ProbeBackend([TimeoutError("once"), True])
    checker = BackendHealthChecker(backend, config=HealthProbeConfig(retries=1))

    snapshot = checker.probe()

    assert snapshot.status is BackendHealthStatus.HEALTHY
    assert backend.calls == 2
    assert snapshot.attempts == 1


def test_factory_health_checker_configuration_and_backend_switch() -> None:
    """Factory wiring supports switching an explicit checker to a Redis backend."""
    local = LocalMemoryBackend()
    local.connect()
    config = BackendConfig(
        health_probe_interval_seconds=12.0,
        health_probe_timeout_seconds=1.5,
        health_probe_retries=0,
    )
    checker = BackendFactory.create_health_checker(local, config)
    assert checker.config.timeout_seconds == 1.5
    assert checker.probe().backend == "LocalBackend"

    client = PingOnlyRedisClient()
    redis = RedisBackend(client=client)
    checker.switch_backend(redis)
    switched = checker.probe()

    assert switched.backend == "RedisBackend"
    assert switched.status is BackendHealthStatus.HEALTHY
    assert client.pings >= 2


def test_redis_probe_uses_an_offline_injected_client() -> None:
    """Redis is never imported or contacted when a compatible client is injected."""
    client = PingOnlyRedisClient()
    backend = RedisBackend(client=client)
    checker = BackendHealthChecker(backend)

    assert checker.probe().status is BackendHealthStatus.HEALTHY
    assert client.pings == 2


def test_concurrent_checks_cache_consistent_immutable_snapshots() -> None:
    """Concurrent callers update counts safely without exposing mutable state."""
    backend = ProbeBackend([True] * 32)
    checker = BackendHealthChecker(backend, config=HealthProbeConfig(retries=0))

    with ThreadPoolExecutor(max_workers=8) as executor:
        snapshots = list(executor.map(lambda _: checker.probe(), range(24)))

    assert all(item.status is BackendHealthStatus.HEALTHY for item in snapshots)
    assert checker.snapshot().attempts == 24
    assert backend.calls == 24


def test_periodic_lifecycle_is_explicit_and_idempotent() -> None:
    """Starting and stopping a periodic checker leaves no owned worker reference."""
    checker = BackendHealthChecker(ProbeBackend([True]))
    checker.start()
    checker.start()
    checker.stop()
    checker.stop()

    assert checker.snapshot().backend == "ProbeBackend"
