"""FastAPI-compatible Enterprise AI Model Platform routes."""

from typing import Any

from model_platform import ModelPlatform, ModelScope


def register_model_routes(app: Any, platform: ModelPlatform) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["models"])

    def scope(tenant: str, workspace: str, actor: str = "dashboard") -> ModelScope:
        return ModelScope(tenant, workspace, actor)

    def listed(values: Any) -> dict[str, Any]:
        data = [value.to_dict() for value in values]
        return {"data": data, "total": len(data), "error": None}

    add(
        "/models",
        lambda tenant, workspace, actor="dashboard": listed(
            platform.list_models(scope(tenant, workspace, actor))
        ),
        ["GET"],
    )
    add(
        "/models",
        lambda payload: platform.register_model(
            dict(payload),
            scope(
                str(payload["tenant"]),
                str(payload["workspace"]),
                str(payload.get("actor", "dashboard")),
            ),
        ).to_dict(),
        ["POST"],
    )
    add("/model-providers", lambda: listed(platform.providers.values()), ["GET"])
    add("/model-profiles", lambda: listed(platform.profiles.values()), ["GET"])
    add("/model-deployments", lambda: listed(platform.deployments.values()), ["GET"])
    add("/model-routing", lambda: listed(platform.routes.values()), ["GET"])
    add(
        "/model-fallback",
        lambda: {
            "data": [
                {
                    "profile_id": item.id,
                    "models": (item.default_model, *item.fallback_models),
                    "retries": item.retries,
                }
                for item in platform.profiles.values()
            ]
        },
        ["GET"],
    )
    add("/model-evaluations", lambda: listed(platform.evaluations.values()), ["GET"])
    add("/model-benchmarks", lambda: listed(platform.benchmarks.values()), ["GET"])
    add(
        "/model-usage",
        lambda tenant, workspace: listed(
            item
            for item in platform.usage
            if item.tenant == tenant and item.workspace == workspace
        ),
        ["GET"],
    )
    add(
        "/model-cost",
        lambda tenant, workspace, actor="dashboard": platform.budget_status(
            scope(tenant, workspace, actor)
        ),
        ["GET"],
    )
    add("/model-governance", lambda: listed(platform.governance.values()), ["GET"])
    add(
        "/model-platform",
        lambda tenant, workspace, actor="dashboard": platform.dashboard(
            scope(tenant, workspace, actor)
        ),
        ["GET"],
    )


__all__ = ("register_model_routes",)
