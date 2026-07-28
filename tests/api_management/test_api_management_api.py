"""API management route contract tests."""

from api_management import ApiManagementPlatform
from api_management.api import register_api_management_routes


class App:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, endpoint: object, methods: list[str], tags: list[str]
    ) -> None:
        assert tags == ["api-management"]
        self.routes.append((path, endpoint, tuple(methods)))


def test_api_contract_and_create_managed_api() -> None:
    app = App()
    register_api_management_routes(app, ApiManagementPlatform())
    paths = {path for path, _, _ in app.routes}
    assert {
        "/api-management/apis",
        "/api-management/gateways",
        "/api-management/routes",
        "/api-management/versions",
        "/api-management/policies",
        "/api-management/keys",
        "/api-management/tokens",
        "/api-management/quotas",
        "/api-management/rate-limits",
        "/api-management/subscriptions",
        "/api-management/analytics",
    } <= paths
    create = next(
        endpoint
        for path, endpoint, methods in app.routes
        if path == "/api-management/apis" and methods == ("POST",)
    )
    result = create(
        {
            "id": "api-a",
            "name": "API A",
            "description": "Managed API",
            "owner": "platform",
            "tenant": "tenant-a",
            "workspace": "workspace-a",
            "version": "1.0.0",
            "base_path": "/a",
            "permissions": "api-management:write",
        }
    )
    assert result["status"] == "draft"
