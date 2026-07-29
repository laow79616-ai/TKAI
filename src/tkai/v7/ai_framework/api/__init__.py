"""GET-only API projections for the V7 unified AI framework."""

from __future__ import annotations

from typing import Any

from ..contracts import Scope
from ..framework import GLOBAL_AI_FRAMEWORK, UnifiedAIFramework

AI_ENDPOINTS = (
    "providers",
    "models",
    "templates",
    "sessions",
    "evaluation",
    "governance",
    "safety",
    "metrics",
)


def register_ai_framework_routes(
    app: Any, framework: UnifiedAIFramework | None = None
) -> None:
    selected = framework or GLOBAL_AI_FRAMEWORK
    for endpoint in AI_ENDPOINTS:

        def read_projection(
            tenant: str, workspace: str, namespace: str = "ai", endpoint: str = endpoint
        ) -> object:
            return selected.projection(endpoint, Scope(tenant, workspace, namespace))

        app.add_api_route(
            f"/v7/ai/{endpoint}",
            read_projection,
            methods=["GET"],
            tags=["V7 Unified AI Framework"],
        )


__all__ = ("AI_ENDPOINTS", "register_ai_framework_routes")
