"""Framework-neutral Enterprise AI multi-agent API routes."""

from typing import Any

from multi_agent import (
    Agent,
    AgentStatus,
    AgentTeam,
    MultiAgentPlatform,
    MultiAgentScope,
    TeamRole,
)


def register_multi_agent_routes(app: Any, platform: MultiAgentPlatform) -> None:
    """Register the public API without requiring FastAPI at import time."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["multi-agent"])

    def scope(payload: dict[str, Any], permission: str) -> MultiAgentScope:
        return MultiAgentScope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("actor", "api")),
            frozenset(str(payload.get("permissions", permission)).split(",")),
        )

    def create_agent(payload: dict[str, Any]) -> dict[str, Any]:
        item = Agent(
            str(payload["id"]),
            str(payload["name"]),
            str(payload.get("description", "")),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["owner"]),
            TeamRole(str(payload["role"])),
            tuple(payload.get("capabilities", ())),
            AgentStatus(str(payload.get("status", "draft"))),
            str(payload.get("version", "1.0.0")),
            dict(payload.get("metadata", {})),
        )
        return platform.create_agent(
            item, scope(payload, "multi_agent:write")
        ).to_dict()

    def create_team(payload: dict[str, Any]) -> dict[str, Any]:
        item = AgentTeam(
            str(payload["id"]),
            str(payload["name"]),
            str(payload.get("description", "")),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["owner"]),
            {
                str(agent_id): TeamRole(str(role))
                for agent_id, role in dict(payload["members"]).items()
            },
            dict(payload.get("metadata", {})),
        )
        return platform.create_team(item, scope(payload, "multi_agent:write")).to_dict()

    def list_agents(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "multi_agent:read",
    ) -> dict[str, Any]:
        request_scope = MultiAgentScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )
        data = [item.to_dict() for item in platform.list_agents(request_scope)]
        return {"data": data, "total": len(data), "error": None}

    def section(name: str) -> Any:
        return lambda tenant, workspace: {
            "section": name,
            "data": platform.dashboard(MultiAgentScope(tenant, workspace, "api")).get(
                name, []
            ),
        }

    add("/multi-agent/agents", list_agents, ["GET"])
    add("/multi-agent/agents", create_agent, ["POST"])
    add("/multi-agent/teams", create_team, ["POST"])
    for name in (
        "planning",
        "execution",
        "coordination",
        "consensus",
        "knowledge",
        "monitoring",
    ):
        dashboard_name = "health" if name == "monitoring" else name
        add(f"/multi-agent/{name}", section(dashboard_name), ["GET"])
    add(
        "/multi-agent/dashboard",
        lambda tenant, workspace: platform.dashboard(
            MultiAgentScope(tenant, workspace, "api")
        ),
        ["GET"],
    )
    add("/multi-agent/metrics", platform.metrics.render_prometheus, ["GET"])


class MultiAgentAPI:
    """Small embeddable API facade used by non-FastAPI runtimes."""

    ROUTES = (
        "/multi-agent/agents",
        "/multi-agent/teams",
        "/multi-agent/planning",
        "/multi-agent/execution",
        "/multi-agent/coordination",
        "/multi-agent/consensus",
        "/multi-agent/knowledge",
        "/multi-agent/monitoring",
    )

    def __init__(self, platform: MultiAgentPlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: MultiAgentScope) -> Any:
        if path not in self.ROUTES:
            raise KeyError(path)
        if path == "/multi-agent/agents":
            return [item.to_dict() for item in self.platform.list_agents(scope)]
        key = "health" if path.endswith("monitoring") else path.rsplit("/", 1)[-1]
        return self.platform.dashboard(scope).get(key, [])


__all__ = ("MultiAgentAPI", "register_multi_agent_routes")
