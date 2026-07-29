"""Read-only HTTP projections for the internal Event Fabric."""

from __future__ import annotations

from typing import Any

from ..framework import GLOBAL_FABRIC, EventFabric

EVENT_RESOURCES = (
    "catalog",
    "registry",
    "publishers",
    "subscribers",
    "subscriptions",
    "routing",
    "dispatch",
    "delivery",
    "retry",
    "dead-letter",
    "replay",
    "ordering",
    "idempotency",
    "health",
    "metrics",
    "lifecycle",
    "audit",
)


def register_event_fabric_routes(app: Any, fabric: EventFabric | None = None) -> None:
    selected = fabric or GLOBAL_FABRIC

    def projection(resource: str) -> Any:
        snapshot = selected.snapshot()
        return snapshot[resource.replace("-", "_")]

    for resource in EVENT_RESOURCES:
        app.add_api_route(
            f"/v7/events/{resource}",
            lambda resource=resource: projection(resource),
            methods=["GET"],
            tags=["V7 Event Fabric"],
        )


__all__ = ("EVENT_RESOURCES", "register_event_fabric_routes")
