"""Framework-neutral cognitive architecture API routes."""

from typing import Any

from cognitive_architecture import (
    CognitiveArchitecturePlatform,
    CognitiveModel,
    CognitiveScope,
    CognitiveStatus,
)


def register_cognitive_routes(
    app: Any, platform: CognitiveArchitecturePlatform
) -> None:
    """Register cognitive routes without requiring FastAPI at import time."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["cognitive"])

    def scope(payload: dict[str, Any], permission: str) -> CognitiveScope:
        return CognitiveScope(
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload.get("actor", "api")),
            frozenset(str(payload.get("permissions", permission)).split(",")),
        )

    def create_model(payload: dict[str, Any]) -> dict[str, Any]:
        model = CognitiveModel(
            str(payload["id"]),
            str(payload["name"]),
            str(payload.get("description", "")),
            str(payload["tenant"]),
            str(payload["workspace"]),
            str(payload["owner"]),
            dict(payload["architecture"]),
            str(payload.get("version", "1.0.0")),
            CognitiveStatus(str(payload.get("status", "draft"))),
            dict(payload.get("metadata", {})),
        )
        return platform.create_model(model, scope(payload, "cognitive:write")).to_dict()

    def list_models(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "cognitive:read",
    ) -> dict[str, Any]:
        request_scope = CognitiveScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )
        data = [item.to_dict() for item in platform.list_models(request_scope)]
        return {"data": data, "total": len(data), "error": None}

    def section(name: str) -> Any:
        return lambda tenant, workspace: {
            "section": name,
            "data": platform.dashboard(CognitiveScope(tenant, workspace, "api")).get(
                name, []
            ),
        }

    add("/cognitive/models", list_models, ["GET"])
    add("/cognitive/models", create_model, ["POST"])
    for name in (
        "perception",
        "memory",
        "reasoning",
        "planning",
        "learning",
        "reflection",
        "decision",
        "monitoring",
    ):
        add(
            f"/cognitive/{name}",
            section("health" if name == "monitoring" else name),
            ["GET"],
        )
    add("/cognitive/metrics", platform.metrics.render_prometheus, ["GET"])


class CognitiveAPI:
    """Embeddable cognitive API facade."""

    ROUTES = (
        "/cognitive/models",
        "/cognitive/perception",
        "/cognitive/memory",
        "/cognitive/reasoning",
        "/cognitive/planning",
        "/cognitive/learning",
        "/cognitive/reflection",
        "/cognitive/decision",
        "/cognitive/monitoring",
    )

    def __init__(self, platform: CognitiveArchitecturePlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: CognitiveScope) -> Any:
        if path not in self.ROUTES:
            raise KeyError(path)
        if path == "/cognitive/models":
            return [item.to_dict() for item in self.platform.list_models(scope)]
        key = "health" if path.endswith("monitoring") else path.rsplit("/", 1)[-1]
        return self.platform.dashboard(scope).get(key, [])


__all__ = ("CognitiveAPI", "register_cognitive_routes")
