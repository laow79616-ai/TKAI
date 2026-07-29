"""GET-only API projections for V7 workflow metadata."""

from __future__ import annotations

from typing import Any

from ..framework import GLOBAL_WORKFLOW_FRAMEWORK, WorkflowFramework

WORKFLOW_RESOURCES = (
    "registry",
    "definitions",
    "planner",
    "dependencies",
    "constraints",
    "history",
    "recovery",
    "health",
    "metrics",
)


def register_workflow_framework_routes(
    app: Any, framework: WorkflowFramework | None = None
) -> None:
    selected = framework or GLOBAL_WORKFLOW_FRAMEWORK
    for resource in WORKFLOW_RESOURCES:
        app.add_api_route(
            f"/v7/workflows/{resource}",
            lambda resource=resource: selected.snapshot()[resource],
            methods=["GET"],
            tags=["V7 Workflow Framework"],
        )


__all__ = ("WORKFLOW_RESOURCES", "register_workflow_framework_routes")
