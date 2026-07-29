"""Read-only dashboard projection for the service mesh."""

from __future__ import annotations

from tkai.v7.service_mesh.contracts import serialize
from tkai.v7.service_mesh.framework import (
    GLOBAL_REGISTRY,
    ServiceRegistry,
    ServiceRouter,
)


class ServiceMeshDashboard:
    sections = (
        "catalog",
        "registry",
        "dependencies",
        "routing",
        "health",
        "metrics",
        "lifecycle",
        "audit",
    )

    def __init__(self, registry: ServiceRegistry | None = None) -> None:
        self.registry = registry or GLOBAL_REGISTRY

    def snapshot(self) -> dict[str, object]:
        services = self.registry.snapshot()
        return {
            "catalog": serialize(services),
            "registry": {
                "total": len(services),
                "indexes": ("category", "owner", "status", "interface"),
            },
            "dependencies": self.registry.graph().as_dict(),
            "routing": ServiceRouter(self.registry).table(),
            "health": {
                service.service_id: serialize(service.health) for service in services
            },
            "metrics": {
                service.service_id: serialize(service.metrics) for service in services
            },
            "lifecycle": {
                service.service_id: serialize(service.lifecycle) for service in services
            },
            "audit": serialize(self.registry.audit.list()),
        }


__all__ = ("ServiceMeshDashboard",)
