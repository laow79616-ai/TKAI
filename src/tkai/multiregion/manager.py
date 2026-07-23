"""Explicit facade for registry, topology, policy, and event publication."""

from __future__ import annotations

from threading import RLock

from tkai.observability import EventBus

from .events import (
    RegionDisabled,
    RegionEnabled,
    RegionEvent,
    RegionFallback,
    RegionRegistered,
    RegionSelected,
    RegionUnavailable,
)
from .models import Region, RegionDecision
from .policy import RegionPolicy
from .registry import RegionRegistry
from .router import MultiRegionRouter
from .topology import RegionTopology


class MultiRegionManager:
    """Manage opt-in local region choice without invoking provider endpoints."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        self.registry = RegionRegistry()
        self.topology = RegionTopology()
        self.policy = RegionPolicy()
        self.router = MultiRegionRouter(self.topology, self.policy)
        self.event_bus = event_bus
        self.events: list[RegionEvent] = []
        self._shutdown = False
        self._lock = RLock()

    def register_region(self, region: Region) -> None:
        self.registry.register(region)
        self._publish(RegionRegistered(region_id=region.region_id, reason="registered"))

    def remove_region(self, region_id: str) -> Region:
        return self.registry.unregister(region_id)

    def select_region(
        self,
        *,
        fixed_region: str | None = None,
        required_capabilities: frozenset[str] = frozenset(),
    ) -> RegionDecision:
        """Run an explicit decision against the current immutable registry view."""
        if self._shutdown:
            raise RuntimeError("MultiRegionManager is shut down")
        try:
            decision = self.router.select(
                self.registry.list(),
                fixed_region=fixed_region,
                required_capabilities=required_capabilities,
            )
        except Exception:
            self._publish(RegionUnavailable(reason="no eligible region"))
            raise
        event_type: type[RegionEvent] = (
            RegionFallback if decision.fallback_used else RegionSelected
        )
        self._publish(
            event_type(
                region_id=decision.selected_region,
                selected_region=decision.selected_region,
                reason=decision.reason,
            )
        )
        return decision

    def enable(self, region_id: str) -> None:
        self.registry.enable(region_id)
        self._publish(RegionEnabled(region_id=region_id, reason="enabled"))

    def disable(self, region_id: str) -> None:
        self.registry.disable(region_id)
        self._publish(RegionDisabled(region_id=region_id, reason="disabled"))

    def snapshot(self) -> dict[str, object]:
        regions = [region.to_dict() for region in self.registry.list()]
        return {
            "enabled": not self._shutdown,
            "regions": regions,
            "topology": self.topology.snapshot(),
            "selected": None,
            "fallback": self.policy.allow_fallback,
        }

    def shutdown(self) -> None:
        with self._lock:
            self._shutdown = True

    def _publish(self, event: RegionEvent) -> None:
        with self._lock:
            self.events.append(event)
        if self.event_bus is not None:
            try:
                self.event_bus.publish(event)
            except Exception:
                return
