"""GET-only API projections for V7 intelligence."""
from __future__ import annotations

from typing import Any

from ..contracts import Scope
from ..framework import GLOBAL_INTELLIGENCE_FRAMEWORK, IntelligenceFramework

INTELLIGENCE_ENDPOINTS = IntelligenceFramework.PROJECTIONS


def register_intelligence_framework_routes(
    app: Any, framework: IntelligenceFramework | None = None
) -> None:
    selected = framework or GLOBAL_INTELLIGENCE_FRAMEWORK
    for endpoint in INTELLIGENCE_ENDPOINTS:
        def read_projection(tenant: str, workspace: str,
                            namespace: str = "intelligence",
                            endpoint: str = endpoint) -> object:
            return selected.projection(endpoint, Scope(tenant, workspace, namespace))
        app.add_api_route(f"/v7/intelligence/{endpoint}", read_projection,
                          methods=["GET"],
                          tags=["V7 Unified Intelligence & Decision Framework"])


__all__ = ("INTELLIGENCE_ENDPOINTS", "register_intelligence_framework_routes")
