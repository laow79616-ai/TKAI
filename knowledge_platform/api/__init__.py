"""FastAPI-compatible knowledge routes."""

from typing import Any

from knowledge_platform.models import Scope
from knowledge_platform.service import KnowledgePlatform


def register_knowledge_routes(app: Any, platform: KnowledgePlatform) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["knowledge"])

    def items(values: tuple[Any, ...]) -> dict[str, Any]:
        data = [item.to_dict() for item in values]
        return {"data": data, "total": len(data), "error": None}

    add(
        "/knowledge-bases",
        lambda tenant, workspace, namespace: items(
            platform.bases.list(Scope(tenant, workspace, namespace))
        ),
        ["GET"],
    )
    add(
        "/knowledge-bases",
        lambda payload: platform.create_base(dict(payload)).to_dict(),
        ["POST"],
    )
    add(
        "/collections",
        lambda tenant, workspace, namespace: items(
            platform.collections.list(Scope(tenant, workspace, namespace))
        ),
        ["GET"],
    )
    add(
        "/documents",
        lambda tenant, workspace, namespace: items(
            platform.documents.list(Scope(tenant, workspace, namespace))
        ),
        ["GET"],
    )
    for path, status in (
        ("/ingestion", "bounded"),
        ("/retrieval", "ready"),
        ("/citations", "stable"),
        ("/connectors", "contracts"),
        ("/evaluation", "available"),
    ):
        add(path, lambda status=status: {"status": status}, ["GET"])
