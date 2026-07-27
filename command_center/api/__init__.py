"""Framework-neutral Enterprise AI Command Center API facade."""

from typing import Any

from ..platform import CommandCenterPlatform, CommandCenterScope


class CommandCenterAPI:
    """Read-only API contract for Command Center operational projections."""

    PREFIX = "/command-center"
    RESOURCES = (
        "overview",
        "control-planes",
        "operations",
        "alerts",
        "incidents",
        "tasks",
        "playbooks",
        "topology",
        "health",
        "activity",
    )
    ROUTES = tuple(f"/command-center/{resource}" for resource in RESOURCES)

    def __init__(self, platform: CommandCenterPlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: CommandCenterScope) -> Any:
        prefix = f"{self.PREFIX}/"
        if not path.startswith(prefix):
            raise KeyError("Unknown Command Center API route.")
        resource = path.removeprefix(prefix)
        if resource not in self.RESOURCES:
            raise KeyError("Unknown Command Center API route.")
        return self.platform.resource(resource, scope)


def register_command_center_routes(app: Any, platform: CommandCenterPlatform) -> None:
    api = CommandCenterAPI(platform)
    for path in api.ROUTES:
        app.add_api_route(
            path,
            lambda tenant, workspace, actor, route=path: api.get(
                route, CommandCenterScope(tenant, workspace, actor)
            ),
            methods=["GET"],
            tags=["command-center"],
        )
