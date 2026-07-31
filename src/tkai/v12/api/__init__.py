"""Complete GET-only TKAI V12 advisory API."""

from __future__ import annotations

from collections.abc import Callable
from functools import partial
from typing import Any

from tkai.v12.platform import V12Platform

GET_ROUTES = (
    "/v12/platform",
    "/v12/platform/components",
    "/v12/platform/health",
    "/v12/platform/readiness",
    "/v12/platform/liveness",
    "/v12/platform/diagnostics",
    "/v12/platform/metrics",
    "/v12/platform/audit",
    "/v12/agents",
    "/v12/agents/profiles",
    "/v12/agents/registry",
    "/v12/agents/discovery",
    "/v12/agents/contexts",
    "/v12/agents/relationships",
    "/v12/agents/dependencies",
    "/v12/agents/coordination",
    "/v12/agents/lifecycle",
    "/v12/agents/health",
    "/v12/agents/diagnostics",
    "/v12/memory",
    "/v12/memory/profiles",
    "/v12/memory/registry",
    "/v12/memory/types",
    "/v12/memory/references",
    "/v12/memory/contexts",
    "/v12/memory/indexes",
    "/v12/memory/provenance",
    "/v12/memory/lineage",
    "/v12/memory/retention",
    "/v12/memory/validation",
    "/v12/memory/health",
    "/v12/skills",
    "/v12/skills/profiles",
    "/v12/skills/registry",
    "/v12/skills/catalog",
    "/v12/skills/discovery",
    "/v12/skills/dependencies",
    "/v12/skills/contracts",
    "/v12/skills/interfaces",
    "/v12/skills/compatibility",
    "/v12/skills/validation",
    "/v12/skills/health",
    "/v12/plugins",
    "/v12/plugins/profiles",
    "/v12/plugins/registry",
    "/v12/plugins/catalog",
    "/v12/plugins/dependencies",
    "/v12/plugins/contracts",
    "/v12/plugins/interfaces",
    "/v12/plugins/compatibility",
    "/v12/plugins/validation",
    "/v12/plugins/security",
    "/v12/workflows",
    "/v12/workflows/profiles",
    "/v12/workflows/registry",
    "/v12/workflows/graphs",
    "/v12/workflows/nodes",
    "/v12/workflows/edges",
    "/v12/workflows/dependencies",
    "/v12/workflows/contexts",
    "/v12/workflows/validation",
    "/v12/workflows/diagnostics",
    "/v12/workflows/readiness",
    "/v12/workflows/health",
    "/v12/models",
    "/v12/models/profiles",
    "/v12/models/registry",
    "/v12/models/capabilities",
    "/v12/models/compatibility",
    "/v12/models/selection",
    "/v12/models/routing",
    "/v12/models/constraints",
    "/v12/models/health",
    "/v12/models/diagnostics",
    "/v12/knowledge",
    "/v12/knowledge/profiles",
    "/v12/knowledge/sources",
    "/v12/knowledge/graphs",
    "/v12/knowledge/indexes",
    "/v12/knowledge/taxonomy",
    "/v12/knowledge/ontology",
    "/v12/knowledge/provenance",
    "/v12/knowledge/lineage",
    "/v12/knowledge/validation",
    "/v12/cognitive",
    "/v12/cognitive/reasoning",
    "/v12/cognitive/decision",
    "/v12/cognitive/planning",
    "/v12/cognitive/evaluation",
    "/v12/cognitive/confidence",
    "/v12/cognitive/uncertainty",
    "/v12/cognitive/contradictions",
    "/v12/cognitive/explanations",
    "/v12/cognitive/limitations",
    "/v12/cognitive/validation",
    "/v12/enterprise",
    "/v12/enterprise/organizations",
    "/v12/enterprise/tenants",
    "/v12/enterprise/workspaces",
    "/v12/enterprise/namespaces",
    "/v12/enterprise/teams",
    "/v12/enterprise/roles",
    "/v12/enterprise/permissions",
    "/v12/enterprise/policies",
    "/v12/enterprise/constraints",
    "/v12/enterprise/boundaries",
    "/v12/enterprise/governance",
    "/v12/enterprise/trust",
    "/v12/enterprise/integrity",
    "/v12/enterprise/compatibility",
    "/v12/enterprise/security",
    "/v12/enterprise/audit",
    "/v12/contracts",
    "/v12/interfaces",
    "/v12/relationships",
    "/v12/dependencies",
    "/v12/compatibility",
    "/v12/governance",
    "/v12/trust",
    "/v12/integrity",
    "/v12/security",
    "/v12/validation",
    "/v12/diagnostics",
    "/v12/health",
    "/v12/metrics",
    "/v12/audit",
    "/v12/lifecycle",
)
FORBIDDEN_METHODS = ("POST", "PUT", "PATCH", "DELETE")


def route_handlers(platform: V12Platform) -> dict[str, Callable[[], object]]:
    handlers: dict[str, Callable[[], object]] = {}
    for path in GET_ROUTES:
        if path == "/v12/platform":
            handlers[path] = platform.overview
        elif path == "/v12/platform/health":
            handlers[path] = platform.health
        elif path == "/v12/platform/readiness":
            handlers[path] = platform.readiness
        elif path == "/v12/platform/liveness":
            handlers[path] = platform.liveness
        elif path == "/v12/platform/diagnostics":
            handlers[path] = platform.diagnostics
        elif path == "/v12/platform/metrics":
            handlers[path] = platform.metrics
        elif path == "/v12/platform/audit":
            handlers[path] = platform.audit
        else:
            handlers[path] = partial(platform.projection, path)
    return handlers


def register_routes(app: Any, platform: V12Platform | None = None) -> V12Platform:
    selected = platform or V12Platform()
    for path, handler in route_handlers(selected).items():
        app.add_api_route(path, handler, methods=["GET"], tags=["TKAI V12"])
    if hasattr(app, "state"):
        app.state.v12_platform = selected
    return selected


def create_router(platform: V12Platform | None = None) -> Any:
    try:
        from fastapi import APIRouter
    except ImportError as error:
        raise RuntimeError("FastAPI is required to create the V12 router.") from error
    router = APIRouter()
    register_routes(router, platform)
    return router


def openapi_contract() -> dict[str, object]:
    return {
        "openapi": "3.1.0",
        "info": {"title": "TKAI V12 Autonomous AI Platform", "version": "12.0.0"},
        "paths": {
            path: {
                "get": {
                    "operationId": "v12_" + path.strip("/").replace("/", "_"),
                    "tags": ["TKAI V12"],
                    "summary": "Read-only advisory metadata projection",
                    "responses": {"200": {"description": "Bounded local metadata"}},
                }
            }
            for path in GET_ROUTES
        },
    }
