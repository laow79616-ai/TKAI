"""FastAPI-compatible Enterprise AI Automation Platform routes."""

from typing import Any

from automation_platform import (
    Action,
    ActionType,
    Automation,
    AutomationPlatform,
    AutomationScope,
    AutomationStatus,
    Pipeline,
    PipelineMode,
    Trigger,
    TriggerType,
)


def register_automation_routes(app: Any, platform: AutomationPlatform) -> None:
    """Register automation routes without importing FastAPI."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["automation"])

    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "automation:read",
    ) -> AutomationScope:
        return AutomationScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )

    def listed(values: Any) -> dict[str, Any]:
        data = [value.to_dict() for value in values]
        return {"data": data, "total": len(data), "error": None}

    def create_automation(payload: dict[str, Any]) -> dict[str, Any]:
        item = Automation(
            str(payload["id"]),
            str(payload["name"]),
            str(payload["description"]),
            str(payload["owner"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["category"]),
            AutomationStatus(str(payload.get("status", "draft"))),
            dict(payload.get("metadata", {})),
        )
        return platform.create_automation(
            item,
            scope(
                item.tenant,
                item.workspace,
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "automation:write")),
            ),
        ).to_dict()

    def create_trigger(payload: dict[str, Any]) -> dict[str, Any]:
        item = Trigger(
            str(payload["id"]),
            str(payload["automation_id"]),
            TriggerType(str(payload["type"])),
            str(payload["tenant"]),
            str(payload["workspace"]),
            dict(payload.get("config", {})),
            bool(payload.get("enabled", True)),
            tuple(payload.get("secret_references", ())),
        )
        return platform.add_trigger(
            item,
            scope(
                item.tenant,
                item.workspace,
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "automation:write")),
            ),
        ).to_dict()

    def create_action(payload: dict[str, Any]) -> dict[str, Any]:
        item = Action(
            str(payload["id"]),
            str(payload["name"]),
            ActionType(str(payload["type"])),
            str(payload["tenant"]),
            str(payload["workspace"]),
            dict(payload.get("config", {})),
            tuple(payload.get("condition_ids", ())),
            tuple(payload.get("secret_references", ())),
            bool(payload.get("requires_approval", False)),
        )
        return platform.add_action(
            item,
            scope(
                item.tenant,
                item.workspace,
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "automation:write")),
            ),
        ).to_dict()

    def create_pipeline(payload: dict[str, Any]) -> dict[str, Any]:
        item = Pipeline(
            str(payload["id"]),
            str(payload["name"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            tuple(payload["action_ids"]),
            PipelineMode(str(payload.get("mode", "sequential"))),
            int(payload.get("retry_limit", 0)),
            bool(payload.get("rollback_on_failure", True)),
            bool(payload.get("checkpoint", False)),
            (
                float(payload["timeout_seconds"])
                if payload.get("timeout_seconds") is not None
                else None
            ),
        )
        return platform.add_pipeline(
            item,
            scope(
                item.tenant,
                item.workspace,
                str(payload.get("actor", "api")),
                str(payload.get("permissions", "automation:write")),
            ),
        ).to_dict()

    def get_history(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "automation:read",
    ) -> dict[str, Any]:
        return listed(platform.history(scope(tenant, workspace, actor, permissions)))

    add(
        "/automation",
        lambda tenant, workspace, actor="api", permissions="automation:read": listed(
            platform.list_automations(scope(tenant, workspace, actor, permissions))
        ),
        ["GET"],
    )
    add("/automation", create_automation, ["POST"])
    add("/triggers", create_trigger, ["POST"])
    add("/actions", create_action, ["POST"])
    add("/pipelines", create_pipeline, ["POST"])
    add("/history", get_history, ["GET"])
    add(
        "/automation/dashboard",
        lambda tenant, workspace, actor="api", permissions="automation:read": (
            platform.dashboard(scope(tenant, workspace, actor, permissions))
        ),
        ["GET"],
    )
    add("/automation/metrics", platform.metrics.render_prometheus, ["GET"])


__all__ = ("register_automation_routes",)
