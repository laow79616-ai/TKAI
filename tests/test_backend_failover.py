"""Offline coverage for explicit distributed backend failover behavior."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from tkai.distributed import (
    BackendFactory,
    BackendHealthChecker,
    FailoverConfig,
    FailoverManager,
    FailoverState,
    FailoverStateError,
    HealthProbeConfig,
    LocalMemoryBackend,
    RedisBackend,
)
from tkai.observability import EventBus


class ToggleBackend:
    """Offline backend double whose health can be changed deterministically."""

    def __init__(self, outcomes: list[bool]) -> None:
        self.outcomes = outcomes
        self.connected = False
        self.probes = 0

    def connect(self) -> None:
        self.connected = True

    def probe_health(self, *, timeout_seconds: float | None = None) -> bool:
        del timeout_seconds
        self.probes += 1
        return self.outcomes.pop(0) if self.outcomes else True


class ToggleRedisClient:
    """Minimal injected Redis client; it performs no network activity."""

    def __init__(self, healthy: bool = True) -> None:
        self.healthy = healthy
        self.pings = 0

    def ping(self) -> bool:
        self.pings += 1
        if not self.healthy:
            raise RuntimeError("offline redis")
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


def checker(backend: ToggleBackend | RedisBackend) -> BackendHealthChecker:
    """Create a one-attempt checker so each test outcome is deterministic."""
    return BackendHealthChecker(backend, config=HealthProbeConfig(retries=0))


def test_primary_healthy_keeps_the_primary_backend_active() -> None:
    """Healthy primary probes never alter the initial routing priority."""
    primary = ToggleBackend([True])
    manager = FailoverManager(primary, health_checker=checker(primary))

    snapshot = manager.evaluate()

    assert snapshot.state is FailoverState.PRIMARY_ACTIVE
    assert manager.active_backend is primary
    assert snapshot.metrics.failovers == 0


def test_failure_threshold_activates_local_memory_fallback() -> None:
    """Only the configured number of consecutive failures triggers failover."""
    primary = ToggleBackend([False, False])
    manager = FailoverManager(
        primary,
        config=FailoverConfig(failure_threshold=2),
        health_checker=checker(primary),
    )

    assert manager.evaluate().state is FailoverState.PRIMARY_ACTIVE
    snapshot = manager.evaluate()

    assert snapshot.state is FailoverState.SECONDARY_ACTIVE
    assert isinstance(manager.active_backend, LocalMemoryBackend)
    assert manager.active_backend.probe_health()
    assert snapshot.consecutive_failures == 2


def test_failover_events_and_metrics_are_published_once() -> None:
    """The single state transition creates one safe event and one metric increment."""
    primary = ToggleBackend([False])
    bus = EventBus()
    manager = FailoverManager(
        primary,
        config=FailoverConfig(failure_threshold=1),
        health_checker=checker(primary),
        event_bus=bus,
    )

    snapshot = manager.evaluate()

    assert snapshot.metrics.failovers == 1
    assert [event.name for event in bus.events] == ["BackendFailedOver"]


def test_recovery_threshold_requires_manual_failback() -> None:
    """Recovery is detected automatically but failback remains caller controlled."""
    primary = ToggleBackend([False, True, True])
    manager = FailoverManager(
        primary,
        config=FailoverConfig(failure_threshold=1, recovery_threshold=2),
        health_checker=checker(primary),
    )

    manager.evaluate()
    assert manager.evaluate().state is FailoverState.SECONDARY_ACTIVE
    recovered = manager.evaluate()

    assert recovered.state is FailoverState.PRIMARY_RECOVERED
    assert manager.active_backend is manager.secondary
    failed_back = manager.manual_failback()
    assert failed_back.state is FailoverState.PRIMARY_ACTIVE
    assert manager.active_backend is primary
    assert failed_back.metrics.failbacks == 1


def test_manual_failback_rejects_invalid_state_transitions() -> None:
    """A primary that was never recovered cannot be manually failed back."""
    primary = ToggleBackend([True])
    manager = FailoverManager(primary, health_checker=checker(primary))

    with pytest.raises(FailoverStateError, match="recovered primary"):
        manager.manual_failback()


def test_consecutive_failures_and_recoveries_reset_on_opposite_results() -> None:
    """Interleaved outcomes cannot accumulate across successful opposite probes."""
    primary = ToggleBackend([False, True, False, False, True, False, True, True])
    manager = FailoverManager(
        primary,
        config=FailoverConfig(failure_threshold=2, recovery_threshold=2),
        health_checker=checker(primary),
    )

    assert manager.evaluate().consecutive_failures == 1
    assert manager.evaluate().consecutive_failures == 0
    manager.evaluate()
    assert manager.evaluate().state is FailoverState.SECONDARY_ACTIVE
    assert manager.evaluate().consecutive_recoveries == 1
    assert manager.evaluate().consecutive_recoveries == 0
    assert manager.evaluate().state is FailoverState.SECONDARY_ACTIVE
    assert manager.evaluate().state is FailoverState.PRIMARY_RECOVERED


def test_fake_redis_failure_fails_over_and_later_recovers_offline() -> None:
    """Redis switching uses only an injected fake client and health probes."""
    client = ToggleRedisClient(healthy=False)
    primary = RedisBackend(client=client, reconnect_attempts=0)
    manager = FailoverManager(
        primary,
        config=FailoverConfig(failure_threshold=1, recovery_threshold=1),
        health_checker=checker(primary),
    )

    assert manager.evaluate().state is FailoverState.SECONDARY_ACTIVE
    client.healthy = True
    assert manager.evaluate().state is FailoverState.PRIMARY_RECOVERED
    assert client.pings >= 2


def test_concurrent_evaluations_produce_one_failover_transition() -> None:
    """Locking prevents concurrent failure checks from duplicating a transition."""
    primary = ToggleBackend([False] * 32)
    manager = FailoverManager(
        primary,
        config=FailoverConfig(failure_threshold=1),
        health_checker=checker(primary),
    )

    with ThreadPoolExecutor(max_workers=8) as executor:
        snapshots = list(executor.map(lambda _: manager.evaluate(), range(16)))

    assert manager.snapshot().state is FailoverState.SECONDARY_ACTIVE
    assert manager.snapshot().metrics.failovers == 1
    assert all(item.metrics.evaluations >= 1 for item in snapshots)


def test_factory_and_periodic_lifecycle_are_explicit_and_idempotent() -> None:
    """Factory construction and worker lifecycle do not alter a backend by default."""
    primary = ToggleBackend([True])
    manager = BackendFactory.create_failover_manager(
        primary, config=FailoverConfig(interval_seconds=10.0)
    )
    manager.start()
    manager.start()
    manager.stop()
    manager.stop()

    assert manager.snapshot().state is FailoverState.PRIMARY_ACTIVE
