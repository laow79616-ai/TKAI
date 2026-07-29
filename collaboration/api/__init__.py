"""FastAPI-compatible Enterprise AI Collaboration Platform routes."""

from typing import Any

from collaboration.models import CollaborationScope
from collaboration.service import EnterpriseAICollaborationPlatform


def register_collaboration_routes(
    app: Any, platform: EnterpriseAICollaborationPlatform
) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["collaboration"])

    def scope(tenant: str, workspace: str, actor: str) -> CollaborationScope:
        return CollaborationScope(tenant, workspace, actor)

    def payload_scope(payload: dict[str, Any]) -> CollaborationScope:
        return scope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["actor"]),
        )

    def listed(values: tuple[Any, ...]) -> dict[str, Any]:
        data = [value.to_dict() for value in values]
        return {"data": data, "total": len(data), "error": None}

    add(
        "/workspaces",
        lambda tenant, workspace, actor: platform.workspaces[
            platform._workspace(scope(tenant, workspace, actor)).id
        ].to_dict(),
        ["GET"],
    )
    add(
        "/workspaces",
        lambda payload: platform.create_workspace(
            dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["POST"],
    )
    add(
        "/projects",
        lambda tenant, workspace, actor: listed(
            platform.list_scoped(
                platform.projects,
                scope(tenant, workspace, actor),
                "collaboration:read",
            )
        ),
        ["GET"],
    )
    add(
        "/projects",
        lambda payload: platform.create_project(
            dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["POST"],
    )
    add(
        "/collaboration",
        lambda tenant, workspace, actor: listed(
            platform.list_scoped(
                platform.sessions,
                scope(tenant, workspace, actor),
                "collaboration:read",
            )
        ),
        ["GET"],
    )
    add(
        "/collaboration",
        lambda payload: platform.create_session(
            dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["POST"],
    )
    add(
        "/collaboration/presence",
        lambda payload: {
            "status": platform.set_presence(
                str(payload["participant"]),
                str(payload["status"]),
                payload_scope(dict(payload)),
            ).value
        },
        ["POST"],
    )
    add(
        "/collaboration/messages",
        lambda payload: platform.send_message(
            dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["POST"],
    )
    add(
        "/collaboration/context/{session_id}",
        lambda session_id, payload: platform.update_context(
            session_id, dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["PATCH"],
    )
    add(
        "/collaboration/handoff",
        lambda payload: platform.handoff(
            dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["POST"],
    )
    add(
        "/tasks",
        lambda tenant, workspace, actor: listed(
            platform.list_scoped(
                platform.tasks,
                scope(tenant, workspace, actor),
                "collaboration:read",
            )
        ),
        ["GET"],
    )
    add(
        "/tasks",
        lambda payload: platform.create_task(
            dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["POST"],
    )
    add(
        "/tasks/{task_id}",
        lambda task_id, payload: platform.update_task(
            task_id, dict(payload), payload_scope(dict(payload))
        ).to_dict(),
        ["PATCH"],
    )
    add(
        "/timeline",
        lambda tenant, workspace, actor: listed(
            platform.timeline_for(scope(tenant, workspace, actor))
        ),
        ["GET"],
    )
    add(
        "/notifications",
        lambda tenant, workspace, actor: listed(
            platform.list_scoped(
                platform.notifications,
                scope(tenant, workspace, actor),
                "collaboration:read",
            )
        ),
        ["GET"],
    )
    add(
        "/collaboration/dashboard",
        lambda tenant, workspace, actor: platform.dashboard(
            scope(tenant, workspace, actor)
        ),
        ["GET"],
    )
