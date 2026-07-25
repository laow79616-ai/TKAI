"""Deterministic in-process soak checks for RC-2, all fully offline."""

from __future__ import annotations

from tkai.cache import CacheEntry, CacheManager
from tkai.observability import Event, EventBus
from tkai.plugins import Hook, PluginManager, PluginMetadata
from tkai.routing import ProviderMetadata, RoutingManager


class _Plugin:
    def initialize(self) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def on_hook(self, hook: Hook, payload: dict[str, object]) -> None:
        return None


def test_one_hundred_thousand_routing_decisions_complete() -> None:
    """Run the target routing volume without state growth or provider calls."""
    manager = RoutingManager()
    manager.register(ProviderMetadata("local", capabilities=frozenset({"chat"})))
    for _ in range(100_000):
        decision = manager.route(required_capabilities=frozenset({"chat"}))
        assert decision.candidate_providers == ("local",)


def test_one_hundred_thousand_cache_reads_complete_with_explicit_history_cleanup() -> (
    None
):
    """Run target cache volume while exercising the documented local cleanup API."""
    manager = CacheManager()
    manager.set(CacheEntry("local", "value"))
    backend = manager.registry.get()
    for number in range(100_000):
        assert manager.get("local") is not None
        if number % 1_000 == 0:
            backend.events.clear()
    assert backend.size() == 1


def test_one_hundred_thousand_event_and_plugin_dispatches_complete() -> None:
    """Exercise bus and hook dispatch at target volume without external work."""
    bus = EventBus()
    plugin_manager = PluginManager()
    plugin_manager.register_sdk(_Plugin(), PluginMetadata("local", "1"))
    for number in range(100_000):
        bus.publish(Event("soak"))
        plugin_manager.dispatch(Hook.BEFORE_REQUEST, {"number": number})
        if number % 1_000 == 0:
            bus.clear()
    assert len(plugin_manager.names()) == 1
