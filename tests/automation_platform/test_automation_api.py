from automation_platform import AutomationPlatform
from automation_platform.api import register_automation_routes


class App:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object, tuple[str, ...]]] = []

    def add_api_route(
        self, path: str, endpoint: object, methods: list[str], tags: list[str]
    ) -> None:
        assert tags == ["automation"]
        self.routes.append((path, endpoint, tuple(methods)))


def test_api_contract_and_handlers() -> None:
    app = App()
    register_automation_routes(app, AutomationPlatform())
    assert {"/automation", "/triggers", "/actions", "/pipelines", "/history"} <= {
        path for path, _, _ in app.routes
    }
    create = next(
        endpoint
        for path, endpoint, methods in app.routes
        if path == "/automation" and methods == ("POST",)
    )
    result = create(
        {
            "id": "auto-a",
            "name": "Automation",
            "description": "Enterprise automation",
            "owner": "platform",
            "tenant": "tenant-a",
            "workspace": "workspace-a",
            "category": "operations",
        }
    )
    assert result["status"] == "draft"
