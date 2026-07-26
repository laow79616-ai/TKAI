"""FastAPI-compatible memory engine API."""

from __future__ import annotations

from typing import Any

from ..models import MemoryScope, SearchQuery
from ..service import EnterpriseAIMemoryEngine


def register_memory_routes(app: Any, service: EnterpriseAIMemoryEngine) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["memory"])

    def scope(tenant: str, workspace: str, owner: str) -> MemoryScope:
        return MemoryScope(tenant, workspace, owner)

    add(
        "/memory",
        lambda tenant, workspace, owner, namespace=None: {
            "data": [
                memory.to_dict()
                for memory in service.list(
                    scope(tenant, workspace, owner), namespace=namespace
                )
            ]
        },
        ["GET"],
    )
    add(
        "/memory",
        lambda payload: service.create(
            dict(payload),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload["owner"]),
            ),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/memory/search",
        lambda payload: {
            "data": [
                result.to_dict()
                for result in service.search(
                    SearchQuery(
                        text=str(payload.get("text", "")),
                        mode=str(payload.get("mode", "hybrid")),
                        namespace=payload.get("namespace"),
                        metadata=dict(payload.get("metadata", {})),
                        top_k=int(payload.get("top_k", 10)),
                        threshold=float(payload.get("threshold", 0)),
                    ),
                    scope(
                        str(payload["tenant"]),
                        str(payload["workspace"]),
                        str(payload["owner"]),
                    ),
                )
            ]
        },
        ["POST"],
    )
    add("/memory/cache", lambda: service.cache.snapshot(), ["GET"])
    add(
        "/memory/retention",
        lambda tenant, workspace, owner: {
            "expired": service.cleanup(scope(tenant, workspace, owner))
        },
        ["POST"],
    )
    add(
        "/memory/namespaces",
        lambda tenant, workspace, owner: {
            "data": service.namespaces.list(scope(tenant, workspace, owner))
        },
        ["GET"],
    )
