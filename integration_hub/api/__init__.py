"""Framework-neutral Integration Hub API facade."""

from typing import Any

from ..platform import HubScope, IntegrationHub


class IntegrationHubAPI:
    ROUTES = (
        "/integration-hub/catalog",
        "/integration-hub/connectors",
        "/integration-hub/instances",
        "/integration-hub/mappings",
        "/integration-hub/flows",
        "/integration-hub/credentials",
        "/integration-hub/health",
        "/integration-hub/schedules",
        "/integration-hub/dead-letter",
        "/integration-hub/analytics",
    )

    def __init__(self, hub: IntegrationHub) -> None:
        self.hub = hub

    def get(self, path: str, scope: HubScope) -> Any:
        resource = path.removeprefix("/integration-hub/").replace("-", "_")
        dashboard = self.hub.dashboard(scope)
        if resource in dashboard:
            return dashboard[resource]
        raise KeyError("Unknown Integration Hub API route.")


def register_integration_hub_routes(app: Any, hub: IntegrationHub) -> None:
    """Register catalog/dashboard endpoints on a FastAPI-like application."""

    api = IntegrationHubAPI(hub)
    for path in api.ROUTES:
        app.add_api_route(
            path,
            lambda tenant, workspace, actor, route=path: api.get(
                route, HubScope(tenant, workspace, actor)
            ),
            methods=["GET"],
            tags=["integration-hub"],
        )
