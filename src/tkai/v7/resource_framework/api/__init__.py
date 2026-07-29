"""GET-only API projections for V7 resource metadata."""

from __future__ import annotations

from typing import Any

from ..framework import GLOBAL_RESOURCE_FRAMEWORK, ResourceFramework

RESOURCE_ENDPOINTS = (
    "catalog",
    "registry",
    "capacity",
    "reservations",
    "dependencies",
    "recovery",
    "health",
    "metrics",
)


def register_resource_framework_routes(
    app: Any, framework: ResourceFramework | None = None
) -> None:
    selected = framework or GLOBAL_RESOURCE_FRAMEWORK
    for endpoint in RESOURCE_ENDPOINTS:
        app.add_api_route(
            f"/v7/resources/{endpoint}",
            lambda endpoint=endpoint: selected.snapshot()[endpoint],
            methods=["GET"],
            tags=["V7 Resource Framework"],
        )


__all__ = ("RESOURCE_ENDPOINTS", "register_resource_framework_routes")
