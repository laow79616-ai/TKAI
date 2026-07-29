"""Framework-neutral Business Intelligence API facade."""

from typing import Any

from ..platform import BIScope, BusinessIntelligencePlatform


class BusinessIntelligenceAPI:
    PREFIX = "/business-intelligence"
    RESOURCES = (
        "workspaces",
        "data-sources",
        "datasets",
        "semantic-models",
        "metrics",
        "queries",
        "reports",
        "dashboards",
        "insights",
        "alerts",
        "subscriptions",
        "exports",
        "governance",
    )
    ROUTES = tuple(f"/business-intelligence/{resource}" for resource in RESOURCES)

    def __init__(self, platform: BusinessIntelligencePlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: BIScope) -> Any:
        prefix = f"{self.PREFIX}/"
        if not path.startswith(prefix):
            raise KeyError("Unknown Business Intelligence API route.")
        resource = path.removeprefix(prefix)
        if resource not in self.RESOURCES:
            raise KeyError("Unknown Business Intelligence API route.")
        return self.platform.resource(resource, scope)


def register_business_intelligence_routes(
    app: Any, platform: BusinessIntelligencePlatform
) -> None:
    api = BusinessIntelligenceAPI(platform)
    for path in api.ROUTES:
        app.add_api_route(
            path,
            lambda tenant, workspace, actor, route=path: api.get(
                route, BIScope(tenant, workspace, actor)
            ),
            methods=["GET"],
            tags=["business-intelligence"],
        )
