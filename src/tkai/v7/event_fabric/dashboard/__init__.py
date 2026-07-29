"""Read-only Event Fabric dashboard projection."""

from __future__ import annotations

from ..framework import GLOBAL_FABRIC, EventFabric


class EventFabricDashboard:
    sections = (
        "overview",
        "registry",
        "publishers",
        "subscribers",
        "subscriptions",
        "routing",
        "dispatch",
        "delivery",
        "retry",
        "dead_letter",
        "replay",
        "ordering",
        "idempotency",
        "health",
        "metrics",
        "audit",
        "lifecycle",
    )

    def __init__(self, fabric: EventFabric | None = None) -> None:
        self.fabric = fabric or GLOBAL_FABRIC

    def snapshot(self) -> dict[str, object]:
        value = self.fabric.snapshot()
        return {
            "overview": value["registry"],
            **{section: value[section] for section in self.sections[1:]},
        }


__all__ = ("EventFabricDashboard",)
