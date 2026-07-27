from operations_platform import OperationsPlatform
from operations_platform.api import register_operations_routes


class App:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, endpoint: object, methods: list[str], tags: list[str]
    ) -> None:
        assert tags == ["operations"]
        self.routes.append((path, endpoint, tuple(methods)))


def test_operations_api_contract_and_handlers() -> None:
    app = App()
    platform = OperationsPlatform()
    register_operations_routes(app, platform)
    paths = {path for path, _, _ in app.routes}
    assert {
        "/operations",
        "/health",
        "/backups",
        "/restore",
        "/capacity",
        "/automation",
        "/diagnostics",
        "/events",
        "/reports",
    } <= paths
    post_operations = next(
        endpoint
        for path, endpoint, methods in app.routes
        if path == "/operations" and methods == ("POST",)
    )
    result = post_operations(
        {
            "id": "center-a",
            "name": "Operations",
            "description": "Control plane",
            "owner": "platform",
            "tenant": "tenant-a",
            "workspace": "workspace-a",
        }
    )
    assert result["id"] == "center-a"
    get_operations = next(
        endpoint
        for path, endpoint, methods in app.routes
        if path == "/operations" and methods == ("GET",)
    )
    assert get_operations("tenant-a", "workspace-a")["total"] == 1
