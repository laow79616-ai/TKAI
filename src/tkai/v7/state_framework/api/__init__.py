"""Read-only API projections for V7 state management."""

from __future__ import annotations

from typing import Any

from ..framework import GLOBAL_STATE_FRAMEWORK, StateFramework

STATE_RESOURCES = (
    "registry",
    "lifecycle",
    "transitions",
    "snapshots",
    "history",
    "consistency",
    "recovery",
    "health",
    "metrics",
)


def register_state_framework_routes(
    app: Any, framework: StateFramework | None = None
) -> None:
    selected = framework or GLOBAL_STATE_FRAMEWORK
    for resource in STATE_RESOURCES:
        app.add_api_route(
            f"/v7/state/{resource}",
            lambda resource=resource: selected.snapshot()[resource],
            methods=["GET"],
            tags=["V7 State Framework"],
        )


__all__ = ("STATE_RESOURCES", "register_state_framework_routes")
