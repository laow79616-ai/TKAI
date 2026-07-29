"""Read-only dashboard projection for all capability views."""

from __future__ import annotations

from tkai.v7.capabilities.contracts import serialize
from tkai.v7.capabilities.framework import GLOBAL_REGISTRY, CapabilityRegistry


class CapabilityDashboard:
    sections = (
        "catalog",
        "registry",
        "dependencies",
        "health",
        "metrics",
        "audit",
        "versions",
        "lifecycle",
    )

    def __init__(self, registry: CapabilityRegistry | None = None) -> None:
        self.registry = registry or GLOBAL_REGISTRY

    def snapshot(self) -> dict[str, object]:
        models = self.registry.snapshot()
        return {
            "catalog": serialize(models),
            "registry": {
                "total": len(models),
                "indexes": ("category", "owner", "status", "tag"),
            },
            "dependencies": self.registry.graph().as_dict(),
            "health": {
                model.capability_id: serialize(model.health) for model in models
            },
            "metrics": {
                model.capability_id: serialize(model.metrics) for model in models
            },
            "audit": serialize(self.registry.audit.list()),
            "versions": {model.capability_id: str(model.version) for model in models},
            "lifecycle": {
                model.capability_id: serialize(model.lifecycle) for model in models
            },
        }


__all__ = ("CapabilityDashboard",)
