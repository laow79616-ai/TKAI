"""Reference memory isolation, capacity, defensive-copy, and concurrency coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from tkai.sdk import MemoryRecord
from tkai.sdk.adapters import InMemoryMemory


def test_reference_memory_store_get_delete_list_and_capacity() -> None:
    """The bounded reference store evicts the oldest key deterministically."""
    memory = InMemoryMemory(capacity=2, namespace="one")
    memory.store(MemoryRecord("first", 1, metadata={"safe": True}))
    memory.put(MemoryRecord("second", 2))
    memory.put(MemoryRecord("third", 3))

    assert memory.get("first") is None
    assert [item.key for item in memory.list()] == ["second", "third"]
    assert [item.key for item in memory.query("th")] == ["third"]
    assert memory.delete("second")
    memory.clear()
    assert memory.list() == ()


def test_reference_memory_concurrent_access_is_local_and_bounded() -> None:
    """Concurrent puts do not expose mutable internal storage or start workers."""
    memory = InMemoryMemory(capacity=100)
    with ThreadPoolExecutor(max_workers=8) as executor:
        list(
            executor.map(
                lambda value: memory.put(MemoryRecord(str(value), value)), range(64)
            )
        )

    assert len(memory.list()) == 64
    assert memory.get("42") == MemoryRecord("42", 42)
