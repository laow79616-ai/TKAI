"""Read-only FastAPI integration for capability operations."""

from __future__ import annotations

from typing import Any

from tkai.v7.capabilities.contracts import serialize
from tkai.v7.capabilities.framework import GLOBAL_REGISTRY, CapabilityRegistry


def register_capability_routes(
    app: Any, registry: CapabilityRegistry | None = None
) -> None:
    """Register GET-only routes without requiring FastAPI at import time."""
    selected = registry or GLOBAL_REGISTRY

    def models() -> list[dict[str, object]]:
        return [serialize(model) for model in selected.snapshot()]

    app.add_api_route(
        "/v7/capabilities/catalog",
        lambda: {"items": models(), "total": len(selected.list())},
        methods=["GET"],
        tags=["V7 Capabilities"],
    )
    app.add_api_route(
        "/v7/capabilities/registry",
        lambda: {
            "items": models(),
            "indexes": ("category", "owner", "status", "tag"),
        },
        methods=["GET"],
        tags=["V7 Capabilities"],
    )
    app.add_api_route(
        "/v7/capabilities/health",
        lambda: {
            "items": [
                {
                    "capability_id": model.capability_id,
                    "health": serialize(selected.health.check(model.capability_id)),
                }
                for model in selected.list()
            ]
        },
        methods=["GET"],
        tags=["V7 Capabilities"],
    )
    app.add_api_route(
        "/v7/capabilities/metrics",
        lambda: {
            "items": [
                {
                    "capability_id": model.capability_id,
                    "metrics": serialize(selected.metrics.get(model.capability_id)),
                }
                for model in selected.list()
            ]
        },
        methods=["GET"],
        tags=["V7 Capabilities"],
    )
    app.add_api_route(
        "/v7/capabilities/lifecycle",
        lambda: {
            "items": [
                {
                    "capability_id": model.capability_id,
                    "status": model.status.value,
                    "history": serialize(model.lifecycle),
                }
                for model in selected.list()
            ]
        },
        methods=["GET"],
        tags=["V7 Capabilities"],
    )
    app.add_api_route(
        "/v7/capabilities/dependencies",
        lambda: {"graph": selected.graph().as_dict()},
        methods=["GET"],
        tags=["V7 Capabilities"],
    )
    app.add_api_route(
        "/v7/capabilities/versions",
        lambda: {
            "items": [
                {
                    "capability_id": model.capability_id,
                    "version": str(model.version),
                    "upgrade_paths": serialize(model.upgrade_paths),
                    "deprecation": serialize(model.deprecation),
                }
                for model in selected.list()
            ]
        },
        methods=["GET"],
        tags=["V7 Capabilities"],
    )
    app.add_api_route(
        "/v7/capabilities/audit",
        lambda: {"items": serialize(selected.audit.list())},
        methods=["GET"],
        tags=["V7 Capabilities"],
    )


__all__ = ("register_capability_routes",)
