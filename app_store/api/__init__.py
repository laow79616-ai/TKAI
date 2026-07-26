"""FastAPI-compatible Enterprise App Store routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app_store.dashboard import dashboard
from app_store.models import Scope
from app_store.service import EnterpriseAppStore


def register_app_store_routes(app: Any, store: EnterpriseAppStore) -> None:
    def route(path: str, endpoint: Callable[..., Any], methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["app-store"])

    def scope(tenant: str, organization: str, workspace: str) -> Scope:
        return Scope(tenant, organization, workspace)

    route(
        "/app-store",
        lambda tenant, organization, workspace: dashboard(
            store, scope(tenant, organization, workspace)
        ),
        ["GET"],
    )
    route(
        "/app-store/applications",
        lambda tenant, organization, workspace, query="": _list(
            store.catalog(scope(tenant, organization, workspace), query=query)
        ),
        ["GET"],
    )
    route(
        "/app-store/applications",
        lambda payload: store.create_application(dict(payload)).to_dict(),
        ["POST"],
    )
    route(
        "/app-store/publishers",
        lambda: _list(tuple(store.publishers.values())),
        ["GET"],
    )
    route(
        "/app-store/publishers",
        lambda payload: store.create_publisher(dict(payload)).to_dict(),
        ["POST"],
    )
    route("/app-store/packages", lambda: _list(tuple(store.packages.values())), ["GET"])
    route(
        "/app-store/installations",
        lambda: _list(tuple(store.installations.values())),
        ["GET"],
    )
    route(
        "/app-store/updates",
        lambda: {
            "data": [],
            "policy": "manual",
            "channels": ["stable", "beta", "private"],
        },
        ["GET"],
    )
    route("/app-store/licenses", lambda: _list(tuple(store.licenses.values())), ["GET"])
    route(
        "/app-store/subscriptions",
        lambda: _list(tuple(store.subscriptions.values())),
        ["GET"],
    )
    route("/app-store/reviews", lambda: _list(tuple(store.reviews.values())), ["GET"])
    route(
        "/app-store/moderation",
        lambda: {
            "submitted": [
                item.to_dict()
                for item in store.applications.values()
                if item.status.value in {"submitted", "under_review"}
            ]
        },
        ["GET"],
    )


def _list(items: tuple[Any, ...]) -> dict[str, Any]:
    data = [item.to_dict() for item in items]
    return {"data": data, "total": len(data), "error": None}
