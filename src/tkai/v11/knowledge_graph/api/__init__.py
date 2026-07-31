"""GET-only transport adapter for the V11 Autonomous Knowledge Graph."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

from tkai.v11.knowledge_graph import AutonomousKnowledgeGraph

RESOURCES = (
    "profile",
    "nodes",
    "edges",
    "relationships",
    "dependencies",
    "taxonomy",
    "ontology",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
)
GET_ROUTES = ("/v11/graph", *(f"/v11/graph/{item}" for item in RESOURCES))
FORBIDDEN_METHODS = ("post", "put", "patch", "delete")
FORBIDDEN_ENDPOINT_TERMS = (
    "execute",
    "action",
    "login",
    "browser",
    "deploy",
    "schedule",
    "allocate",
    "mutate",
    "control",
    "tiktok",
)


def _project(graph: AutonomousKnowledgeGraph, handler: Callable[[], object]) -> object:
    """Serialize a handler result without exposing handler parameters to FastAPI."""
    return graph.projection(handler())


def route_handlers(
    graph: AutonomousKnowledgeGraph,
) -> dict[str, Callable[[], object]]:
    handlers: dict[str, Callable[[], object]] = {
        "/v11/graph": graph.overview,
        **{
            f"/v11/graph/{resource}": getattr(graph, resource) for resource in RESOURCES
        },
    }
    return {
        path: partial(_project, graph, handler) for path, handler in handlers.items()
    }


def register_routes(
    app: Any, graph: AutonomousKnowledgeGraph | None = None
) -> AutonomousKnowledgeGraph:
    selected = graph or AutonomousKnowledgeGraph()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path,
                handler,
                methods=["GET"],
                tags=["V11 Autonomous Knowledge Graph"],
            )
        else:
            app.get(path, tags=["V11 Autonomous Knowledge Graph"])(handler)
    return selected


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "paths": {
            path: {"get": {"tags": ["V11 Autonomous Knowledge Graph"]}}
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
