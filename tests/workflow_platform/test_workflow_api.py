from workflow_platform import WorkflowPlatform
from workflow_platform.api import register_workflow_routes


class App:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], object] = {}

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        for method in methods:
            self.routes[(method, path)] = endpoint


def test_workflow_api_contract() -> None:
    app = App()
    register_workflow_routes(app, WorkflowPlatform())
    for path in (
        "/workflows",
        "/workflows/history",
        "/workflows/templates",
        "/workflows/forms",
        "/workflows/approvals",
    ):
        assert ("GET", path) in app.routes
    assert ("POST", "/workflows") in app.routes
    assert ("POST", "/workflows/run") in app.routes
