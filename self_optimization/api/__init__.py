"""Framework-neutral self-optimization API routes."""

from typing import Any

from self_optimization import (
    OptimizationProfile,
    OptimizationScope,
    OptimizationStatus,
    SelfOptimizationPlatform,
)


class SelfOptimizationAPI:
    ROUTES = (
        "/self-optimization/profiles",
        "/self-optimization/optimization",
        "/self-optimization/resources",
        "/self-optimization/performance",
        "/self-optimization/cost",
        "/self-optimization/latency",
        "/self-optimization/capacity",
        "/self-optimization/experiments",
        "/self-optimization/recommendations",
        "/self-optimization/monitoring",
    )

    def __init__(self, platform: SelfOptimizationPlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: OptimizationScope) -> Any:
        if path not in self.ROUTES:
            raise KeyError(path)
        return self.platform.dashboard(scope)[path.rsplit("/", 1)[-1]]


def register_self_optimization_routes(
    app: Any, platform: SelfOptimizationPlatform
) -> None:
    """Register public route contracts without importing a web framework."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["self-optimization"])

    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "self_optimization:read",
    ) -> OptimizationScope:
        return OptimizationScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )

    def create_profile(payload: dict[str, Any]) -> dict[str, Any]:
        profile = OptimizationProfile(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            tenant=str(payload["tenant"]),
            workspace=str(payload["workspace"]),
            owner=str(payload["owner"]),
            optimization_target=str(payload["optimization_target"]),
            version=str(payload.get("version", "1.0.0")),
            status=OptimizationStatus(str(payload.get("status", "draft"))),
            metadata=dict(payload.get("metadata", {})),
        )
        request_scope = scope(
            profile.tenant,
            profile.workspace,
            str(payload.get("actor", "api")),
            str(payload.get("permissions", "self_optimization:write")),
        )
        return platform.create_profile(profile, request_scope).to_dict()

    def list_profiles(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "self_optimization:read",
    ) -> dict[str, Any]:
        data = [
            item.to_dict()
            for item in platform.list_profiles(
                scope(tenant, workspace, actor, permissions)
            )
        ]
        return {"data": data, "total": len(data), "error": None}

    def section(name: str) -> Any:
        def endpoint(tenant: str, workspace: str) -> dict[str, Any]:
            return {
                "section": name,
                "data": platform.dashboard(scope(tenant, workspace))[name],
                "error": None,
            }

        return endpoint

    add(SelfOptimizationAPI.ROUTES[0], list_profiles, ["GET"])
    add(SelfOptimizationAPI.ROUTES[0], create_profile, ["POST"])
    for path in SelfOptimizationAPI.ROUTES[1:]:
        add(path, section(path.rsplit("/", 1)[-1]), ["GET"])
    add("/self-optimization/metrics", platform.metrics.render_prometheus, ["GET"])


__all__ = ("SelfOptimizationAPI", "register_self_optimization_routes")
