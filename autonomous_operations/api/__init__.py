"""FastAPI-compatible autonomous operations routes."""

from typing import Any

from autonomous_operations import (
    AutonomousOperation,
    AutonomousOperationsPlatform,
    Objective,
    ObjectiveType,
    OperationMode,
    OperationScope,
    Policy,
    PolicyType,
    Strategy,
    StrategyType,
)


def register_autonomous_operations_routes(
    app: Any, platform: AutonomousOperationsPlatform
) -> None:
    """Register routes without importing FastAPI."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(
            path, endpoint, methods=methods, tags=["autonomous-operations"]
        )

    def scope(payload: dict[str, Any], permission: str) -> OperationScope:
        return OperationScope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("actor", "api")),
            frozenset(str(payload.get("permissions", permission)).split(",")),
        )

    def create_operation(payload: dict[str, Any]) -> dict[str, Any]:
        item = AutonomousOperation(
            str(payload["id"]),
            str(payload["name"]),
            str(payload["description"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["owner"]),
            int(payload.get("priority", 0)),
            OperationMode(str(payload.get("mode", "supervised"))),
            metadata=dict(payload.get("metadata", {})),
        )
        return platform.create_operation(
            item, scope(payload, "autonomous_operations:write")
        ).to_dict()

    def create_objective(payload: dict[str, Any]) -> dict[str, Any]:
        item = Objective(
            str(payload["id"]),
            str(payload["operation_id"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            ObjectiveType(str(payload["type"])),
            float(payload["target"]),
            float(payload.get("weight", 1)),
            str(payload.get("unit", "")),
            payload.get("custom_name"),
        )
        return platform.add_objective(
            item, scope(payload, "autonomous_operations:write")
        ).to_dict()

    def create_policy(payload: dict[str, Any]) -> dict[str, Any]:
        item = Policy(
            str(payload["id"]),
            str(payload["operation_id"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            PolicyType(str(payload["type"])),
            dict(payload.get("rules", {})),
        )
        return platform.add_policy(
            item, scope(payload, "autonomous_operations:write")
        ).to_dict()

    def create_strategy(payload: dict[str, Any]) -> dict[str, Any]:
        item = Strategy(
            str(payload["id"]),
            str(payload["operation_id"]),
            str(payload["tenant"]),
            str(payload["workspace"]),
            StrategyType(str(payload["type"])),
            dict(payload.get("config", {})),
        )
        return platform.add_strategy(
            item, scope(payload, "autonomous_operations:write")
        ).to_dict()

    def listed(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "autonomous_operations:read",
    ) -> dict[str, Any]:
        request_scope = OperationScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )
        data = [item.to_dict() for item in platform.list_operations(request_scope)]
        return {"data": data, "total": len(data), "error": None}

    add("/autonomous-operations", listed, ["GET"])
    add("/autonomous-operations", create_operation, ["POST"])
    add("/autonomous-operations/objectives", create_objective, ["POST"])
    add("/autonomous-operations/policies", create_policy, ["POST"])
    add("/autonomous-operations/strategies", create_strategy, ["POST"])
    for path in ("executions", "feedback", "optimization", "learning", "safety"):
        add(
            f"/autonomous-operations/{path}",
            lambda tenant, workspace, section=path: {
                "section": section,
                "data": platform.dashboard(
                    OperationScope(tenant, workspace, "api")
                ).get(section, []),
            },
            ["GET"],
        )
    add(
        "/autonomous-operations/dashboard",
        lambda tenant, workspace: platform.dashboard(
            OperationScope(tenant, workspace, "api")
        ),
        ["GET"],
    )
    add("/autonomous-operations/metrics", platform.metrics.render_prometheus, ["GET"])


__all__ = ("register_autonomous_operations_routes",)
