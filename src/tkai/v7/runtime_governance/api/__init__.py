"""GET-only API projections for V7 runtime governance metadata."""

from __future__ import annotations

from typing import Any

from ..contracts import Scope
from ..framework import GLOBAL_RUNTIME_GOVERNANCE, RuntimeGovernanceFramework

RUNTIME_GOVERNANCE_ENDPOINTS = RuntimeGovernanceFramework.PROJECTIONS


def register_runtime_governance_routes(
    app: Any, framework: RuntimeGovernanceFramework | None = None
) -> None:
    selected = framework or GLOBAL_RUNTIME_GOVERNANCE
    for endpoint in RUNTIME_GOVERNANCE_ENDPOINTS:

        def read_projection(
            tenant: str,
            workspace: str,
            namespace: str = "runtime-governance",
            endpoint: str = endpoint,
        ) -> object:
            return selected.projection(endpoint, Scope(tenant, workspace, namespace))

        app.add_api_route(
            f"/v7/runtime-governance/{endpoint}",
            read_projection,
            methods=["GET"],
            tags=["V7 Unified Runtime Governance Framework"],
        )


__all__ = (
    "RUNTIME_GOVERNANCE_ENDPOINTS",
    "register_runtime_governance_routes",
)
