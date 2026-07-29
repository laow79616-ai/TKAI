"""GET-only API projections for V7 configuration metadata."""

from __future__ import annotations

from typing import Any

from ..contracts import Scope
from ..framework import GLOBAL_CONFIGURATION_FRAMEWORK, ConfigurationFramework

CONFIGURATION_ENDPOINTS = (
    "registry",
    "environments",
    "profiles",
    "sources",
    "precedence",
    "schemas",
    "defaults",
    "overrides",
    "effective",
    "validation",
    "snapshots",
    "versions",
    "diff",
    "change-plans",
    "compatibility",
    "migration",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)


def register_configuration_framework_routes(
    app: Any, framework: ConfigurationFramework | None = None
) -> None:
    selected = framework or GLOBAL_CONFIGURATION_FRAMEWORK
    for endpoint in CONFIGURATION_ENDPOINTS:

        def read_projection(
            tenant: str, workspace: str, namespace: str, endpoint: str = endpoint
        ) -> object:
            return selected.projection(endpoint, Scope(tenant, workspace, namespace))

        app.add_api_route(
            f"/v7/configuration/{endpoint}",
            read_projection,
            methods=["GET"],
            tags=["V7 Configuration Framework"],
        )


__all__ = ("CONFIGURATION_ENDPOINTS", "register_configuration_framework_routes")
