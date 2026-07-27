"""Framework-neutral general intelligence API routes."""

from typing import Any

from general_intelligence import (
    GeneralIntelligencePlatform,
    IntelligenceProfile,
    IntelligenceScope,
    IntelligenceStatus,
)


class GeneralIntelligenceAPI:
    ROUTES = (
        "/general-intelligence/profiles",
        "/general-intelligence/capabilities",
        "/general-intelligence/reasoning",
        "/general-intelligence/planning",
        "/general-intelligence/learning",
        "/general-intelligence/execution",
        "/general-intelligence/evaluation",
        "/general-intelligence/monitoring",
    )

    def __init__(self, platform: GeneralIntelligencePlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: IntelligenceScope) -> Any:
        if path not in self.ROUTES:
            raise KeyError(path)
        if path.endswith("profiles"):
            return [item.to_dict() for item in self.platform.list_profiles(scope)]
        key = path.rsplit("/", 1)[-1]
        return self.platform.dashboard(scope)[key]


def register_general_intelligence_routes(
    app: Any, platform: GeneralIntelligencePlatform
) -> None:
    """Register required routes without importing FastAPI."""

    def add(path: str, endpoint: Any, methods: list[str]) -> None:
        app.add_api_route(
            path, endpoint, methods=methods, tags=["general-intelligence"]
        )

    def request_scope(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "general_intelligence:read",
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
            architecture=str(
                payload.get("architecture", "enterprise-general-intelligence")
            ),
            version=str(payload.get("version", "1.0.0")),
            status=IntelligenceStatus(str(payload.get("status", "draft"))),
            metadata=dict(payload.get("metadata", {})),
        )
        scope = IntelligenceScope(
            profile.tenant,
            profile.workspace,
            str(payload.get("actor", "api")),
            frozenset(
                str(
                    payload.get(
                        "permissions", "general_intelligence:write"
                    )
                ).split(",")
            ),
        )
        return platform.create_profile(profile, scope).to_dict()

    def list_profiles(
        tenant: str,
        workspace: str,
        actor: str = "api",
        permissions: str = "general_intelligence:read",
    ) -> dict[str, Any]:
        data = [
            item.to_dict()
            for item in platform.list_profiles(
                request_scope(tenant, workspace, actor, permissions)
            )
        ]
        return {"data": data, "total": len(data), "error": None}

    def section(name: str) -> Any:
        def endpoint(tenant: str, workspace: str) -> dict[str, Any]:
            data = platform.dashboard(request_scope(tenant, workspace))[name]
            return {"section": name, "data": data, "error": None}

        return endpoint

    add(GeneralIntelligenceAPI.ROUTES[0], list_profiles, ["GET"])
    add(GeneralIntelligenceAPI.ROUTES[0], create_profile, ["POST"])
    for path in GeneralIntelligenceAPI.ROUTES[1:]:
        add(path, section(path.rsplit("/", 1)[-1]), ["GET"])
    add(
        "/general-intelligence/metrics",
        platform.metrics.render_prometheus,
        ["GET"],
    )


__all__ = (
    "GeneralIntelligenceAPI",
    "register_general_intelligence_routes",
)
