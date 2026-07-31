"""GET-only API for the V11 Autonomous Reasoning Fabric."""

from collections.abc import Callable
from functools import partial
from typing import Any

from tkai.v11.reasoning_fabric import AutonomousReasoningFabric

RESOURCES = (
    "profiles",
    "contexts",
    "claims",
    "premises",
    "evidence",
    "inferences",
    "assumptions",
    "constraints",
    "alternatives",
    "contradictions",
    "confidence",
    "uncertainty",
    "explanations",
    "evaluations",
    "relationships",
    "knowledge-graph",
    "compatibility",
    "governance",
    "trust",
    "integrity",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)
GET_ROUTES = ("/v11/reasoning", *(f"/v11/reasoning/{name}" for name in RESOURCES))
FORBIDDEN_METHODS = ("post", "put", "patch", "delete")
FORBIDDEN_ENDPOINT_TERMS = (
    "execute",
    "decision-execution",
    "planning-execution",
    "policy-execution",
    "approve",
    "migration",
    "upgrade",
    "rollback",
    "mutate",
    "apply",
    "workflow-start",
    "schedule",
    "allocate",
    "service-start",
    "service-stop",
    "service-restart",
    "deploy",
    "recover",
    "secret-value",
    "hidden-reasoning",
    "chain-of-thought",
    "private-scratchpad",
    "hidden-prompt",
    "internal-system-message",
    "graph-mutation",
)


def _project(
    fabric: AutonomousReasoningFabric, handler: Callable[[], object]
) -> object:
    return fabric.projection(handler())


def route_handlers(
    fabric: AutonomousReasoningFabric,
) -> dict[str, Callable[[], object]]:
    handlers: dict[str, Callable[[], object]] = {"/v11/reasoning": fabric.overview}
    for resource in RESOURCES:
        method_name = {
            "profiles": "profile",
            "knowledge-graph": "knowledge_graph",
        }.get(resource, resource)
        handlers[f"/v11/reasoning/{resource}"] = getattr(fabric, method_name)
    return {
        path: partial(_project, fabric, handler) for path, handler in handlers.items()
    }


def register_routes(
    app: Any, fabric: AutonomousReasoningFabric | None = None
) -> AutonomousReasoningFabric:
    selected = fabric or AutonomousReasoningFabric()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(
            path, handler, methods=["GET"], tags=["V11 Autonomous Reasoning Fabric"]
        )
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V11 Autonomous Reasoning Fabric"]}}
            for path in GET_ROUTES
        },
    }


def validate_forbidden_endpoints() -> bool:
    paths = openapi_contract()["paths"]
    assert isinstance(paths, dict)
    return all(
        not any(term in path for term in FORBIDDEN_ENDPOINT_TERMS)
        and not any(method in operations for method in FORBIDDEN_METHODS)
        for path, operations in paths.items()
    )


__all__ = (
    "FORBIDDEN_ENDPOINT_TERMS",
    "FORBIDDEN_METHODS",
    "GET_ROUTES",
    "RESOURCES",
    "openapi_contract",
    "register_routes",
    "route_handlers",
    "validate_forbidden_endpoints",
)
