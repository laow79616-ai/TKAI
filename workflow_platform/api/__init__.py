"""FastAPI-compatible workflow routes."""

from typing import Any

from workflow_platform.models import Scope
from workflow_platform.service import WorkflowPlatform


def register_workflow_routes(app: Any, platform: WorkflowPlatform) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["workflows"])

    def scope(payload: dict[str, Any]) -> Scope:
        return Scope(str(payload["tenant"]), str(payload["workspace"]))

    add(
        "/workflows",
        lambda tenant, workspace: {
            "data": [
                item.to_dict() for item in platform.list(Scope(tenant, workspace))
            ],
            "error": None,
        },
        ["GET"],
    )
    add(
        "/workflows",
        lambda payload: platform.create(dict(payload)).to_dict(),
        ["POST"],
    )
    add(
        "/workflows/run",
        lambda payload: platform.run(
            str(payload["workflow_id"]),
            scope(payload),
            dict(payload.get("input", {})),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/workflows/history",
        lambda tenant, workspace: {
            "data": [
                item.to_dict()
                for item in platform.history.list(Scope(tenant, workspace))
            ]
        },
        ["GET"],
    )
    for path, value in (
        ("/workflows/templates", platform.templates.search),
        ("/workflows/forms", lambda: {"status": "available"}),
        ("/workflows/approvals", lambda: {"status": "available"}),
    ):
        add(path, value, ["GET"])
