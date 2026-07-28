"""Framework-neutral Digital Twin API facade."""

from typing import Any

from ..platform import DigitalTwinPlatform, TwinScope


class DigitalTwinAPI:
    ROUTES = (
        "/digital-twins",
        "/entities",
        "/relationships",
        "/state",
        "/simulation",
        "/predictions",
        "/optimization",
    )

    def __init__(self, platform: DigitalTwinPlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: TwinScope) -> Any:
        dashboard = self.platform.dashboard(scope)
        aliases = {
            "/digital-twins": "twins",
            "/entities": "topology",
            "/relationships": "topology",
            "/state": "twins",
        }
        resource = aliases.get(path, path.removeprefix("/"))
        if resource in dashboard:
            return dashboard[resource]
        raise KeyError("Unknown Digital Twin API route.")


def register_digital_twin_routes(
    app: Any, platform: DigitalTwinPlatform
) -> None:
    """Register dashboard endpoints on a FastAPI-like application."""

    api = DigitalTwinAPI(platform)
    for path in api.ROUTES:
        app.add_api_route(
            path,
            lambda tenant, workspace, actor, route=path: api.get(
                route, TwinScope(tenant, workspace, actor)
            ),
            methods=["GET"],
            tags=["digital-twin"],
        )
