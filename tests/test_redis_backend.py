"""Offline unit and integration-style coverage for the optional Redis backend."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from tkai.distributed import (
    BackendConfig,
    BackendFactory,
    DistributedCoordinator,
    LocalBackend,
    LocalMemoryBackend,
    Node,
    RedisBackend,
    RedisBackendOperationError,
    RedisBackendUnavailableError,
    create_backend,
)


class FakeRedisClient:
    """Small deterministic redis-py replacement that never accesses a network."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.published: list[tuple[str, str]] = []
        self.closed = False
        self.ping_count = 0
        self.fail_get_once = False

    def ping(self) -> bool:
        self.ping_count += 1
        return True

    def get(self, key: str) -> bytes | None:
        if self.fail_get_once:
            self.fail_get_once = False
            raise RuntimeError("temporary local test failure")
        value = self.values.get(key)
        return None if value is None else value.encode("utf-8")

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
        self.published.append((topic, value))
        return 1

    def close(self) -> None:
        self.closed = True


def test_local_backend_remains_factory_default_and_compatibility_alias() -> None:
    """Default construction remains the original in-memory implementation."""
    assert isinstance(BackendFactory.create(), LocalBackend)
    assert isinstance(create_backend(BackendConfig()), LocalMemoryBackend)
    assert LocalMemoryBackend is LocalBackend


def test_redis_backend_uses_injected_client_without_network() -> None:
    """Exercise data, notifications, lock ownership, and external lifecycle."""
    client = FakeRedisClient()
    backend = RedisBackend(client=client, namespace="test")
    received: list[dict[str, int]] = []
    backend.subscribe("updates", received.append)

    backend.connect()
    backend.set("item", {"value": 1})
    backend.publish("updates", {"value": 2})

    assert backend.get("item") == {"value": 1}
    assert backend.delete("item")
    assert backend.get("item") is None
    assert client.published == [("test:topic:updates", '{"value":2}')]
    assert received == [{"value": 2}]
    assert backend.acquire_lock("resource", "one")
    assert backend.acquire_lock("resource", "one")
    assert not backend.acquire_lock("resource", "two")
    assert not backend.release_lock("resource", "two")
    assert backend.release_lock("resource", "one")
    assert backend.health()

    backend.disconnect()
    backend.disconnect()
    assert not backend.health()
    assert not client.closed


def test_redis_backend_reconnects_once_after_a_transient_operation_failure() -> None:
    """Reconnect logic is bounded and does not sleep or reach a real service."""
    client = FakeRedisClient()
    backend = RedisBackend(client=client, reconnect_attempts=1)
    backend.connect()
    backend.set("value", "present")
    client.fail_get_once = True

    assert backend.get("value") == "present"
    assert client.ping_count == 2


def test_redis_backend_rejects_non_json_values_and_wraps_operation_errors() -> None:
    """Unsafe serialization and exhausted local failures use clear typed errors."""
    backend = RedisBackend(client=FakeRedisClient(), reconnect_attempts=0)
    backend.connect()
    with pytest.raises(RedisBackendOperationError, match="JSON-compatible"):
        backend.set("bad", object())


def test_redis_backend_missing_optional_dependency_is_explicit(monkeypatch) -> None:
    """The optional package is only required when a default client is requested."""
    backend = RedisBackend()

    def unavailable() -> FakeRedisClient:
        raise RedisBackendUnavailableError("missing redis")

    monkeypatch.setattr(backend, "_create_client", unavailable)
    with pytest.raises(RedisBackendUnavailableError, match="missing redis"):
        backend.connect()


def test_redis_backend_closes_only_clients_it_created(monkeypatch) -> None:
    """Lifecycle ownership closes an internally-created client exactly once."""
    client = FakeRedisClient()
    backend = RedisBackend()
    monkeypatch.setattr(backend, "_create_client", lambda: client)

    backend.connect()
    backend.close()
    backend.close()

    assert client.closed


def test_redis_backend_async_wrappers_and_coordinator_integration() -> None:
    """Async wrappers and the existing coordinator use the new backend unchanged."""
    client = FakeRedisClient()
    backend = RedisBackend(client=client)

    async def exercise() -> None:
        await backend.aconnect()
        await backend.aset("value", [1, 2])
        assert await backend.aget("value") == [1, 2]
        assert await backend.adelete("value")
        await backend.adisconnect()

    asyncio.run(exercise())

    now = datetime.now(timezone.utc)
    coordinator = DistributedCoordinator(
        Node("redis-node", "localhost", now, now), backend=backend
    )
    coordinator.start()
    assert coordinator.summary()["backend"] == "RedisBackend"
    coordinator.stop()


def test_backend_factory_builds_redis_without_changing_local_behavior() -> None:
    """Factory construction accepts injected clients and validates immutable config."""
    client = FakeRedisClient()
    backend = BackendFactory.create(
        BackendConfig(kind="redis", namespace="factory", reconnect_attempts=0),
        client=client,
    )
    assert isinstance(backend, RedisBackend)
    backend.connect()
    backend.set("key", True)
    assert backend.get("key") is True
    with pytest.raises(ValueError, match="timeout_seconds"):
        BackendConfig(timeout_seconds=0)
