"""GET-only API projections for the V7 data framework."""

from __future__ import annotations

from typing import Any

from ..contracts import Scope
from ..framework import GLOBAL_DATA_FRAMEWORK, UnifiedDataFramework

DATA_ENDPOINTS = UnifiedDataFramework.PROJECTIONS


def register_data_framework_routes(
    app: Any, framework: UnifiedDataFramework | None = None
) -> None:
    selected = framework or GLOBAL_DATA_FRAMEWORK
    for endpoint in DATA_ENDPOINTS:

        def read_projection(
            tenant: str,
            workspace: str,
            namespace: str = "data",
            endpoint: str = endpoint,
        ) -> object:
            return selected.projection(endpoint, Scope(tenant, workspace, namespace))

        app.add_api_route(
            f"/v7/data/{endpoint}",
            read_projection,
            methods=["GET"],
            tags=["V7 Unified Data & Storage Framework"],
        )


__all__ = ("DATA_ENDPOINTS", "register_data_framework_routes")
