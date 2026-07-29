"""GET-only API projections for V7 extension metadata."""

from __future__ import annotations

from typing import Any

from ..contracts import Scope
from ..framework import GLOBAL_EXTENSION_FRAMEWORK, ExtensionFramework

EXTENSION_ENDPOINTS = (
    "catalog",
    "registry",
    "plugins",
    "dependencies",
    "compatibility",
    "validation",
    "packages",
    "signatures",
    "health",
    "metrics",
    "audit",
)


def register_extension_framework_routes(
    app: Any, framework: ExtensionFramework | None = None
) -> None:
    selected = framework or GLOBAL_EXTENSION_FRAMEWORK
    for endpoint in EXTENSION_ENDPOINTS:

        def read_projection(
            tenant: str,
            workspace: str,
            namespace: str = "extensions",
            endpoint: str = endpoint,
        ) -> object:
            return selected.projection(endpoint, Scope(tenant, workspace, namespace))

        app.add_api_route(
            f"/v7/extensions/{endpoint}",
            read_projection,
            methods=["GET"],
            tags=["V7 Extension Framework"],
            summary=f"Read V7 extension {endpoint} metadata",
        )


__all__ = ("EXTENSION_ENDPOINTS", "register_extension_framework_routes")
