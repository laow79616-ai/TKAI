"""FastAPI-compatible Application Center routes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from applications.dashboard import dashboard
from applications.service import ApplicationCenter


def register_application_routes(app: Any, center: ApplicationCenter) -> None:
    def route(path: str, endpoint: Callable[..., Any], methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["applications"])

    route("/applications", lambda: _list(center.catalog.list()), ["GET"])
    route(
        "/applications",
        lambda payload: center.create(dict(payload)).to_dict(),
        ["POST"],
    )
    route("/applications/dashboard", lambda: dashboard(center), ["GET"])
    route("/applications/versions", lambda: _list(center.versions.list()), ["GET"])
    route(
        "/applications/{application_id}",
        lambda application_id: center.catalog.get(application_id).to_dict(),
        ["GET"],
    )
    route(
        "/applications/{application_id}",
        lambda application_id, payload: center.catalog.update(
            application_id, dict(payload)
        ).to_dict(),
        ["PATCH"],
    )
    route(
        "/applications/{application_id}/lifecycle",
        lambda application_id, payload: center.transition(
            application_id, str(payload["status"]), str(payload["actor"])
        ).to_dict(),
        ["POST"],
    )
    route("/templates", lambda: _list(center.templates.list()), ["GET"])
    route("/deployments", lambda: _list(center.deployments.list()), ["GET"])
    route(
        "/deployments",
        lambda payload: center.deployments.deploy(
            str(payload["application_id"]),
            str(payload["version"]),
            str(payload["actor"]),
            environment=str(payload.get("environment", "production")),
            replicas=int(payload.get("replicas", 1)),
            quota=int(payload.get("quota", 1000)),
        ).to_dict(),
        ["POST"],
    )


def _list(values: tuple[Any, ...]) -> dict[str, Any]:
    data = [value.to_dict() for value in values]
    return {"data": data, "total": len(data), "error": None}
