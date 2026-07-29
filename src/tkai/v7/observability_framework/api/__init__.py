"""GET-only API projections for V7 observability metadata."""

from __future__ import annotations

from typing import Any

from ..contracts import ObservationScope
from ..framework import GLOBAL_OBSERVABILITY_FRAMEWORK, ObservabilityFramework

OBSERVABILITY_ENDPOINTS = (
    "metrics",
    "logging",
    "tracing",
    "diagnostics",
    "health",
    "alerts",
    "telemetry",
    "audit",
)


def register_observability_framework_routes(
    app: Any, framework: ObservabilityFramework | None = None
) -> None:
    selected = framework or GLOBAL_OBSERVABILITY_FRAMEWORK
    for endpoint in OBSERVABILITY_ENDPOINTS:

        def read_projection(
            tenant: str, workspace: str, endpoint: str = endpoint
        ) -> object:
            return selected.snapshot(ObservationScope(tenant, workspace))[endpoint]

        app.add_api_route(
            f"/v7/observability/{endpoint}",
            read_projection,
            methods=["GET"],
            tags=["V7 Observability Framework"],
        )


__all__ = ("OBSERVABILITY_ENDPOINTS", "register_observability_framework_routes")
