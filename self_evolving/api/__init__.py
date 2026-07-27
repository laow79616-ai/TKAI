"""Framework-neutral self-evolving API routes."""

from typing import Any

from self_evolving import (
    EvolutionProfile,
    EvolutionScope,
    EvolutionStatus,
    SelfEvolvingPlatform,
)


class SelfEvolvingAPI:
    ROUTES = (
        "/self-evolving/profiles",
        "/self-evolving/evolution",
        "/self-evolving/learning",
        "/self-evolving/experiments",
        "/self-evolving/optimization",
        "/self-evolving/monitoring",
    )

    def __init__(self, platform: SelfEvolvingPlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: EvolutionScope) -> Any:
        if path not in self.ROUTES:
            raise KeyError(path)
        key = path.rsplit("/", 1)[-1]
        return self.platform.dashboard(scope)[key]


def register_self_evolving_routes(app: Any, platform: SelfEvolvingPlatform) -> None:
    """Register the public route contract without importing a web framework."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(path, endpoint, methods=methods, tags=["self-evolving"])

    def scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "self_evolving:read",
    ) -> EvolutionScope:
        return EvolutionScope(
            tenant, workspace, actor, frozenset(permissions.split(","))
        )

    def create_profile(payload: dict[str, Any]) -> dict[str, Any]:
        profile = EvolutionProfile(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            tenant=str(payload["tenant"]),
            workspace=str(payload["workspace"]),
            owner=str(payload["owner"]),
            generation=int(payload.get("generation", 0)),
            capability_level=int(payload["capability_level"]),
            version=str(payload.get("version", "1.0.0")),
            status=EvolutionStatus(str(payload.get("status", "draft"))),
            metadata=dict(payload.get("metadata", {})),
        )
        request_scope = scope(
            profile.tenant,
            profile.workspace,
            str(payload.get("actor", "api")),
            str(payload.get("permissions", "self_evolving:write")),
        )
        return platform.create_profile(profile, request_scope).to_dict()

    def list_profiles(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "self_evolving:read",
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

    add(SelfEvolvingAPI.ROUTES[0], list_profiles, ["GET"])
    add(SelfEvolvingAPI.ROUTES[0], create_profile, ["POST"])
    for path in SelfEvolvingAPI.ROUTES[1:]:
        add(path, section(path.rsplit("/", 1)[-1]), ["GET"])
    add("/self-evolving/metrics", platform.metrics.render_prometheus, ["GET"])


__all__ = ("SelfEvolvingAPI", "register_self_evolving_routes")
