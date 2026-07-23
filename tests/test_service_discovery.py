"""Offline regression coverage for explicit local and Redis service discovery."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from tkai.distributed import (
    BackendFactory,
    FailoverManager,
    LocalMemoryBackend,
    LocalServiceRegistry,
    RedisBackend,
    RedisServiceRegistry,
    ServiceInstance,
    ServiceInstanceNotFoundError,
)

NOW = datetime(2099, 7, 23, tzinfo=timezone.utc)


class FakeRedisClient:
    """Small local Redis double used without importing or contacting Redis."""

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


def instance(
    instance_id: str = "one",
    *,
    service: str = "api",
    ttl_seconds: float = 30.0,
    version: str | None = None,
    region: str | None = None,
    tags: frozenset[str] = frozenset(),
    metadata: dict[str, str] | None = None,
) -> ServiceInstance:
    """Build deterministic UTC-safe discovery records for all local tests."""
    return ServiceInstance.create(
        service,
        instance_id,
        f"http://{instance_id}.local",
        ttl_seconds=ttl_seconds,
        version=version,
        region=region,
        tags=tags,
        metadata=metadata,
        now=NOW,
    )


def test_local_registration_lookup_and_deregistration() -> None:
    """Register, look up, then remove one stable service record."""
    registry = LocalServiceRegistry()
    registered = registry.register(instance())

    assert registry.lookup("api") == (registered,)
    assert registry.deregister("api", "one")
    assert registry.lookup("api") == ()
    assert not registry.deregister("api", "one")


def test_heartbeat_renew_refreshes_ttl_and_missing_records_are_explicit() -> None:
    """Renew uses immutable replacement data and reports absent instances clearly."""
    registry = LocalServiceRegistry()
    registry.register(instance(ttl_seconds=5.0))
    renewed = registry.renew(
        "api", "one", ttl_seconds=10.0, now=NOW + timedelta(seconds=2)
    )

    assert renewed.expires_at == NOW + timedelta(seconds=12)
    with pytest.raises(ServiceInstanceNotFoundError, match="not registered"):
        registry.renew("api", "missing", ttl_seconds=1.0, now=NOW)


def test_ttl_expiration_cleanup_and_snapshot_are_stable() -> None:
    """Expired records are purged and snapshots expose no mutable internals."""
    registry = LocalServiceRegistry()
    record = registry.register(instance(ttl_seconds=1.0, metadata={"tier": "gold"}))

    assert registry.cleanup(now=NOW + timedelta(seconds=1)) == 1
    assert registry.snapshot(now=NOW + timedelta(seconds=1)) == ()
    with pytest.raises(TypeError):
        record.metadata["tier"] = "changed"


def test_multi_instance_lookup_filters_version_region_tags_and_metadata() -> None:
    """Lookup applies all supplied metadata filters with deterministic ordering."""
    registry = LocalServiceRegistry()
    registry.register(
        instance(
            "eu-one",
            version="1",
            region="eu",
            tags=frozenset({"blue", "paid"}),
            metadata={"tier": "gold"},
        )
    )
    registry.register(
        instance(
            "us-one",
            version="2",
            region="us",
            tags=frozenset({"green"}),
            metadata={"tier": "silver"},
        )
    )

    found = registry.lookup(
        "api",
        version="1",
        region="eu",
        tags=frozenset({"blue"}),
        metadata={"tier": "gold"},
    )
    assert [item.instance_id for item in found] == ["eu-one"]
    assert [item.instance_id for item in registry.list()] == ["eu-one", "us-one"]


def test_redis_registry_uses_an_offline_injected_redis_backend() -> None:
    """Redis discovery performs JSON-safe registry operations without a real server."""
    backend = RedisBackend(client=FakeRedisClient(), namespace="test")
    registry = RedisServiceRegistry(backend)
    record = registry.register(instance("redis-one", region="apac"))

    assert registry.lookup("api", region="apac") == (record,)
    assert registry.renew("api", "redis-one", ttl_seconds=60.0, now=NOW).expires_at == (
        NOW + timedelta(seconds=60)
    )
    assert registry.deregister("api", "redis-one")
    assert registry.list() == ()


def test_concurrent_registration_and_lookup_are_thread_safe() -> None:
    """Concurrent callers receive stable records without mutation errors."""
    registry = LocalServiceRegistry()

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda number: registry.register(instance(str(number))), range(32)
            )
        )
        results = list(executor.map(lambda _: registry.lookup("api"), range(16)))

    assert all(len(result) == 32 for result in results)
    assert [item.instance_id for item in registry.list()] == sorted(
        str(value) for value in range(32)
    )


def test_factory_selects_local_or_redis_registry_without_changing_failover() -> None:
    """Factory samples an explicit backend without taking over failover."""
    local = BackendFactory.create_service_registry()
    redis = BackendFactory.create_service_registry(
        backend=RedisBackend(client=FakeRedisClient())
    )
    primary = LocalMemoryBackend()
    manager = FailoverManager(primary)
    sampled = BackendFactory.create_service_registry(failover_manager=manager)

    assert isinstance(local, LocalServiceRegistry)
    assert isinstance(redis, RedisServiceRegistry)
    assert isinstance(sampled, LocalServiceRegistry)


def test_registry_lifecycle_cleanup_and_instance_serialization() -> None:
    """Lifecycle calls are idempotent and records round-trip through JSON-ready data."""
    registry = LocalServiceRegistry(cleanup_interval_seconds=10.0)
    record = instance(tags=frozenset({"one"}), metadata={"language": "zh"})
    registry.register(record)
    registry.start()
    registry.start()
    registry.stop()
    registry.stop()

    restored = ServiceInstance.from_dict(record.to_dict())
    assert restored == record
    assert restored.to_dict()["tags"] == ["one"]
