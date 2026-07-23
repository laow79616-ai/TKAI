"""Ensure bounded local resources can be removed and re-used explicitly."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from tkai.adaptive import AdaptiveRoutingManager, ProviderSignal
from tkai.distributed import DistributedCoordinator, LocalBackend, Node
from tkai.multiregion import MultiRegionManager, Region
from tkai.observability import Event, EventBus


def _node() -> Node:
    now = datetime.now(timezone.utc)
    return Node("local", "localhost", now, now)


def test_local_registries_locks_and_subscriptions_clean_up_for_reuse() -> None:
    """Clear or stop each real local resource before building a new operation."""
    bus = EventBus()
    calls: list[str] = []
    bus.subscribe(lambda event: calls.append(event.name))
    bus.publish(Event("before"))
    bus.clear()
    bus.publish(Event("after"))
    assert calls == ["before"]
    assert [event.name for event in bus.events] == ["after"]

    backend = LocalBackend()
    backend.set("value", 1)
    assert backend.delete("value")
    assert backend.get("value") is None
    assert backend.acquire_lock("resource", "one")
    assert backend.release_lock("resource", "one")
    assert backend.acquire_lock("resource", "two")
    assert backend.release_lock("resource", "two")

    adaptive = AdaptiveRoutingManager()
    adaptive.record_signal(ProviderSignal("local", datetime.now(timezone.utc)))
    adaptive.clear()
    assert adaptive.history.snapshot() == ()
    regions = MultiRegionManager()
    regions.register_region(Region("local"))
    regions.registry.clear()
    assert regions.registry.snapshot() == ()

    coordinator = DistributedCoordinator(_node())
    coordinator.register_resource("temporary", object())
    coordinator.registry.clear()
    assert coordinator.registry.list() == []


def test_executor_context_releases_all_workers_after_bounded_local_work() -> None:
    """Use the executor context manager so no worker remains owned by this test."""
    backend = LocalBackend()
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda number: number * number, range(20)))
    assert results == [number * number for number in range(20)]
    assert backend.health() is False
