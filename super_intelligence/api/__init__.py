"""Framework-neutral super intelligence API routes."""

from typing import Any

from super_intelligence import (
    IntelligenceProfile,
    IntelligenceScope,
    IntelligenceStatus,
    SuperIntelligencePlatform,
)


class SuperIntelligenceAPI:
    ROUTES = (
        "/super-intelligence/profiles",
        "/super-intelligence/capabilities",
        "/super-intelligence/reasoning",
        "/super-intelligence/planning",
        "/super-intelligence/world-models",
        "/super-intelligence/prediction",
        "/super-intelligence/optimization",
        "/super-intelligence/evaluation",
        "/super-intelligence/monitoring",
    )

    def __init__(self, platform: SuperIntelligencePlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: IntelligenceScope) -> Any:
        if path not in self.ROUTES:
            raise KeyError(path)
        if path.endswith("profiles"):
            return [item.to_dict() for item in self.platform.list_profiles(scope)]
        return self.platform.dashboard(scope)[path.rsplit("/", 1)[-1]]


def register_super_intelligence_routes(
    app: Any, platform: SuperIntelligencePlatform
) -> None:
    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["super-intelligence"])

    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "super_intelligence:read",
    ) -> IntelligenceScope:
        return IntelligenceScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )

    def create_profile(payload: dict[str, Any]) -> dict[str, Any]:
        profile = IntelligenceProfile(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            tenant=str(payload["tenant"]),
            workspace=str(payload["workspace"]),
            owner=str(payload["owner"]),
            capability_level=int(payload["capability_level"]),
            architecture=str(payload["architecture"]),
            version=str(payload.get("version", "1.0.0")),
            status=IntelligenceStatus(str(payload.get("status", "draft"))),
            metadata=dict(payload.get("metadata", {})),
        )
        request_scope = scope(
            profile.tenant,
            profile.workspace,
            str(payload.get("actor", "api")),
            str(payload.get("permissions", "super_intelligence:write")),
        )
        return platform.create_profile(profile, request_scope).to_dict()

    def list_profiles(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "super_intelligence:read",
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

    add(SuperIntelligenceAPI.ROUTES[0], list_profiles, ["GET"])
    add(SuperIntelligenceAPI.ROUTES[0], create_profile, ["POST"])
    for path in SuperIntelligenceAPI.ROUTES[1:]:
        add(path, section(path.rsplit("/", 1)[-1]), ["GET"])
    add("/super-intelligence/metrics", platform.metrics.render_prometheus, ["GET"])


__all__ = ("SuperIntelligenceAPI", "register_super_intelligence_routes")
