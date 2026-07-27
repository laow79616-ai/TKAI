from integration_platform import IntegrationPlatform
from integration_platform.api import register_integration_routes


class App:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, endpoint: object, methods: list[str], tags: list[str]
    ) -> None:
        assert tags == ["integration"]
        self.routes.append((path, endpoint, tuple(methods)))


def test_api_contract_and_create_handler() -> None:
    app = App()
    register_integration_routes(app, IntegrationPlatform())
    paths = {path for path, _, _ in app.routes}
    assert {
        "/integrations",
        "/integration-connectors",
        "/integration-credentials",
        "/integration-webhooks",
        "/integration-events",
        "/integration-messaging",
        "/integration-databases",
        "/integration-storage",
        "/integration-health",
    } <= paths
    create = next(
        endpoint
        for path, endpoint, methods in app.routes
        if path == "/integrations" and methods == ("POST",)
    )
    result = create(
        {
            "id": "crm-a",
            "name": "CRM",
            "description": "CRM connector",
            "provider": "reference",
            "category": "crm",
            "owner": "platform",
            "tenant": "tenant-a",
            "workspace": "workspace-a",
        }
    )
    assert result["status"] == "draft"
