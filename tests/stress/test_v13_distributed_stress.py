"""Bounded concurrent validation for explicit V1.3 distributed components."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from benchmarks.v13_runtime import FakeRedisClient
from tkai.distributed import (
    BackendFactory,
    BackendHealthStatus,
    LocalServiceRegistry,
    RedisBackend,
    ServiceInstance,
)


def test_v13_fake_redis_health_and_registry_are_concurrent_and_bounded() -> None:
    """Use an injected fake client and local registry without network activity."""
    backend = RedisBackend(client=FakeRedisClient())
    checker = BackendFactory.create_health_checker(backend)
    registry = LocalServiceRegistry()
    now = datetime.now(timezone.utc)

    def operate(number: int) -> None:
        backend.set(str(number), number)
        assert backend.get(str(number)) == number
        assert checker.probe().status is BackendHealthStatus.HEALTHY
        record = ServiceInstance.create(
            "api", str(number), f"local://{number}", now=now
        )
        registry.register(record)
        assert registry.lookup("api")
        assert registry.deregister("api", str(number))
        assert backend.delete(str(number))

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(operate, range(48)))

    assert registry.list() == ()
    assert all(backend.get(str(number)) is None for number in range(48))
