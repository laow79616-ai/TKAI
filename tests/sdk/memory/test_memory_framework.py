"""Offline Memory SDK contract, reference implementation, and registry coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest

from tkai.sdk.memory import (
    MemoryConfiguration,
    MemoryFactory,
    MemoryLifecycle,
    MemoryLifecycleError,
    MemoryNamespace,
    MemoryQuery,
    MemoryRecord,
    MemoryRegistry,
    MemorySession,
    MemoryType,
    ReferenceMemory,
)
from tkai.sdk.memory.errors import MemoryNotFoundError


def test_reference_memory_store_get_delete_list_and_snapshot_are_isolated() -> None:
    """The local backend stores data without exposing mutable internal records."""
    memory = ReferenceMemory()
    value = {"items": ["one"]}
    record = MemoryRecord("key", value, metadata={"source": "test"})
    memory.store(record)
    value["items"].append("outside")

    fetched = memory.get("key")
    assert fetched is not None
    assert fetched.value == {"items": ["one"]}
    snapshot = memory.snapshot()
    assert snapshot.records[0].metadata == {"source": "test"}
    assert memory.delete("key")
    assert memory.list().records == ()


def test_namespace_session_capacity_and_local_ttl_are_deterministic() -> None:
    """Namespace/session filters, eviction, and TTL use an injected local clock."""
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    def clock() -> datetime:
        return now

    configuration = MemoryConfiguration(capacity=2, default_ttl_seconds=10)
    memory = ReferenceMemory(configuration=configuration, clock=clock)
    alpha = MemoryNamespace("alpha")
    session = MemorySession("session-a")
    memory.store(MemoryRecord("one", 1, namespace=alpha, session=session))
    memory.store(MemoryRecord("two", 2, namespace=alpha, session=session))
    memory.store(MemoryRecord("three", 3, namespace=alpha, session=session))

    assert tuple(record.key for record in memory.list().records) == ("two", "three")
    assert memory.get("three", MemoryQuery(namespace=alpha, session=session))
    now += timedelta(seconds=11)
    assert memory.list().records == ()


def test_registry_factory_and_lifecycle_are_explicit_and_thread_safe() -> None:
    """Registries and factories create only caller-selected local memories."""
    factory = MemoryFactory()
    factory.register("reference", lambda config: ReferenceMemory(configuration=config))
    memory = factory.create("reference", MemoryConfiguration(capacity=4))
    registry = MemoryRegistry()
    registry.register(memory)
    assert registry.lookup("reference-memory") is memory
    assert registry.unregister("reference-memory") is memory
    with pytest.raises(MemoryNotFoundError):
        registry.lookup("reference-memory")

    memory.close()
    memory.close()
    assert memory.lifecycle is MemoryLifecycle.CLOSED
    with pytest.raises(MemoryLifecycleError):
        memory.store(MemoryRecord("closed", None))

    concurrent = MemoryRegistry()
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda index: concurrent.register(ReferenceMemory(f"memory-{index}")),
                range(32),
            )
        )
    assert [item.name for item in concurrent.list()] == sorted(
        f"memory-{index}" for index in range(32)
    )


def test_memory_types_and_filtered_clear_remain_local() -> None:
    """Memory category declarations and filtered cleanup require no external service."""
    memory = ReferenceMemory()
    first = MemoryNamespace("first")
    memory.store(
        MemoryRecord("short", 1, memory_type=MemoryType.SHORT_TERM, namespace=first)
    )
    memory.store(MemoryRecord("long", 2, memory_type=MemoryType.LONG_TERM))
    memory.clear(MemoryQuery(namespace=first))
    assert memory.get("short", MemoryQuery(namespace=first)) is None
    assert memory.get("long") is not None
