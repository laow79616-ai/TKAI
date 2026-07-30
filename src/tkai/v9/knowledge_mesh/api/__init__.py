"""GET-only transport adapter for the V8 Adaptive Knowledge Mesh."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tkai.v9.knowledge_mesh.contracts import KnowledgeLifecycle
from tkai.v9.knowledge_mesh.fabric import AdaptiveKnowledgeMesh
from tkai.v9.knowledge_mesh.metrics import metrics_snapshot

_RESOURCES = (
    "profiles",
    "federation",
    "ontologies",
    "taxonomies",
    "domains",
    "concepts",
    "entities",
    "relationships",
    "records",
    "evidence",
    "provenance",
    "lineage",
    "semantics",
    "normalization",
    "quality",
    "confidence",
    "versions",
    "compatibility",
    "governance",
    "analytics",
    "diagnostics",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)
GET_ROUTES = tuple(f"/v9/knowledge/{name}" for name in _RESOURCES)


def route_handlers(
    fabric: AdaptiveKnowledgeMesh,
) -> dict[str, Callable[[], object]]:
    def items(name: str) -> dict[str, object]:
        return {"items": fabric.snapshot()[name], "mode": "reference-only"}

    def empty() -> dict[str, object]:
        return {"items": (), "mode": "reference-only"}

    handlers: dict[str, Callable[[], object]] = {route: empty for route in GET_ROUTES}
    handlers.update(
        {
            "/v9/knowledge/profiles": lambda: items("profiles"),
            "/v9/knowledge/federation": lambda: {
                "sources": fabric.snapshot()["sources"],
                "relationships": fabric.snapshot()["relationships"],
                "mode": "reference-only",
            },
            "/v9/knowledge/records": lambda: items("knowledge"),
            "/v9/knowledge/evidence": lambda: items("evidence"),
            "/v9/knowledge/compatibility": lambda: items("compatibility"),
            "/v9/knowledge/confidence": lambda: items("confidence"),
            "/v9/knowledge/diagnostics": lambda: {"items": fabric.diagnostics()},
            "/v9/knowledge/health": fabric.health,
        "/v9/knowledge/metrics": lambda: metrics_snapshot(fabric),
            "/v9/knowledge/audit": lambda: {"items": fabric.snapshot()["audit"]},
            "/v9/knowledge/lifecycle": lambda: {
                "states": tuple(item.value for item in KnowledgeLifecycle),
                "approval_authorizes_execution": False,
            },
        }
    )
    return handlers


def register_routes(
    app: Any, fabric: AdaptiveKnowledgeMesh | None = None
) -> AdaptiveKnowledgeMesh:
    selected = fabric or AdaptiveKnowledgeMesh()
    for path, handler in route_handlers(selected).items():
        if hasattr(app, "add_api_route"):
            app.add_api_route(
                path, handler, methods=["GET"], tags=["V9 Adaptive Knowledge Mesh"]
            )
        else:
            app.get(path, tags=["V9 Adaptive Knowledge Mesh"])(handler)
    return selected


def create_router(fabric: AdaptiveKnowledgeMesh | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the router.") from error
    router = APIRouter()
    register_routes(router, fabric)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "TKAI V9 Adaptive Knowledge Mesh", "version": "9.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "get_" + path.removeprefix("/").replace("/", "_"),
                    "responses": {
                        "200": {"description": "Reference-only knowledge metadata"}
                    },
                }
            }
            for path in GET_ROUTES
        },
    }


__all__ = (
    "GET_ROUTES",
    "create_router",
    "openapi_contract",
    "register_routes",
    "route_handlers",
)
