"""Offline concurrent stress coverage for RC-2 reliability validation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from tkai.cache import CacheEntry, CacheManager
from tkai.observability import Event, EventBus
from tkai.plugins import PluginManager, PluginMetadata
from tkai.rate_limit import RateLimitManager, RateLimitSnapshot
from tkai.routing import ProviderMetadata, RoutingManager


class _Plugin:
    def initialize(self) -> None:
        return None

    def shutdown(self) -> None:
        return None


def test_registries_and_plugins_remain_consistent_under_concurrent_registration() -> (
    None
):
    """Exercise registry locks with unique concurrent registrations."""
    routing = RoutingManager()
    plugins = PluginManager()

    def register(number: int) -> None:
        name = f"provider-{number}"
        routing.register(ProviderMetadata(name))
        plugins.register_sdk(_Plugin(), PluginMetadata(name, "1"))

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(register, range(100)))

    assert len(routing.list()) == 100
    assert len(plugins.names()) == 100
    routing.clear()
    plugins.registry.clear()
    assert routing.list() == []
    assert plugins.names() == []


def test_cache_rate_limit_and_event_bus_are_safe_under_concurrent_use() -> None:
    """Verify concurrent local operations preserve bounded, valid shared state."""
    cache = CacheManager()
    limiter = RateLimitManager()
    limiter.register(RateLimitSnapshot("local", requests_per_minute=1_000))
    bus = EventBus()
    delivered: list[str] = []
    bus.subscribe(lambda event: delivered.append(event.name))

    def operate(number: int) -> bool:
        key = f"key-{number}"
        cache.set(CacheEntry(key, number))
        assert cache.get(key) is not None
        bus.publish(Event("stress"))
        return limiter.consume("local")

    with ThreadPoolExecutor(max_workers=16) as pool:
        allowed = list(pool.map(operate, range(500)))

    assert all(allowed)
    assert limiter.list()[0].current_requests == 500
    assert len(bus.events) == len(delivered) == 500
    cache.registry.clear()
    bus.clear()
    assert cache.registry.get().size() == 0
    assert bus.events == []


def test_repeated_subscription_and_clear_do_not_accumulate_resources() -> None:
    """Exercise explicit cleanup boundaries for in-memory registries and bus state."""
    bus = EventBus()

    def handler(event: Event) -> None:
        return None

    for _ in range(1_000):
        bus.subscribe(handler)
        bus.publish(Event("cleanup"))
        bus.unsubscribe(handler)
        bus.clear()
    assert bus.events == []
