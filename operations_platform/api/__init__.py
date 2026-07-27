"""FastAPI-compatible Enterprise AI Operations Platform routes."""

from typing import Any

from operations_platform import (
    CapacitySnapshot,
    HealthStatus,
    OperationsCenter,
    OperationsPlatform,
    OperationsScope,
)


def register_operations_routes(app: Any, platform: OperationsPlatform) -> None:
    """Register public operations routes without a FastAPI import dependency."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["operations"])

    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "operations:read",
    ) -> OperationsScope:
        return OperationsScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )

    def listed(values: Any) -> dict[str, Any]:
        data = [value.to_dict() for value in values]
        return {"data": data, "total": len(data), "error": None}

    def get_report(
        report_type: str,
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "operations:read",
    ) -> dict[str, Any]:
        return platform.report(
            report_type, scope(tenant, workspace, actor, permissions)
        )

    def get_dashboard(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "operations:read",
    ) -> dict[str, Any]:
        return platform.dashboard(scope(tenant, workspace, actor, permissions))

    add(
        "/operations",
        lambda tenant, workspace, actor="api", permissions="operations:read": listed(
            platform.list_centers(scope(tenant, workspace, actor, permissions))
        ),
        ["GET"],
    )
    add(
        "/operations",
        lambda payload: platform.create_center(
            OperationsCenter(
                str(payload["id"]),
                str(payload["name"]),
                str(payload["description"]),
                str(payload["owner"]),
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("status", "active")),
                dict(payload.get("metadata", {})),
            ),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "operations:write")),
            ),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/health",
        lambda payload: platform.check_health(
            str(payload["component"]),
            str(payload["component_id"]),
            HealthStatus(str(payload["status"])),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "operations:execute")),
            ),
            dict(payload.get("details", {})),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/backups",
        lambda payload: platform.create_backup(
            str(payload["id"]),
            tuple(payload["categories"]),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "operations:execute")),
            ),
            str(payload["schedule"]) if payload.get("schedule") else None,
            int(payload.get("retention_days", 30)),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/backups",
        lambda tenant, workspace, actor="api", permissions="operations:read": listed(
            platform._scoped(
                platform.backups.values(), scope(tenant, workspace, actor, permissions)
            )
        ),
        ["GET"],
    )
    add(
        "/restore",
        lambda payload: platform.restore(
            str(payload["backup_id"]),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "operations:execute")),
            ),
            preview=bool(payload.get("preview", False)),
            approval_id=(
                str(payload["approval_id"]) if payload.get("approval_id") else None
            ),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/capacity",
        lambda payload: platform.record_capacity(
            CapacitySnapshot(
                str(payload["tenant"]),
                str(payload["workspace"]),
                float(payload["cpu"]),
                float(payload["memory"]),
                float(payload["storage"]),
                int(payload["token_usage"]),
                int(payload["queue"]),
                int(payload["concurrency"]),
                dict(payload.get("forecast", {})),
            ),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "operations:execute")),
            ),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/automation",
        lambda payload: platform.schedule_automation(
            str(payload["id"]),
            str(payload["kind"]),
            dict(payload.get("payload", {})),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "operations:write")),
            ),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/diagnostics",
        lambda payload: platform.run_diagnostics(
            tuple(payload["checks"]),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "operations:execute")),
            ),
        ).to_dict(),
        ["POST"],
    )
    add(
        "/events",
        lambda tenant, workspace, actor="api", permissions="operations:read": listed(
            platform._scoped(
                platform.events, scope(tenant, workspace, actor, permissions)
            )
        ),
        ["GET"],
    )
    add(
        "/reports",
        get_report,
        ["GET"],
    )
    add(
        "/operations/dashboard",
        get_dashboard,
        ["GET"],
    )
    add("/operations/metrics", platform.metrics.render_prometheus, ["GET"])


__all__ = ("register_operations_routes",)
