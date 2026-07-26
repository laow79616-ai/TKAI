from applications import ApplicationCenter
from applications.api import register_application_routes


class App:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], object] = {}

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        for method in methods:
            self.routes[(method, path)] = endpoint


def test_application_api_contract() -> None:
    app = App()
    center = ApplicationCenter()
    register_application_routes(app, center)
    for path in (
        "/applications",
        "/templates",
        "/deployments",
        "/applications/versions",
    ):
        assert ("GET", path) in app.routes
    template_endpoint = app.routes[("GET", "/templates")]
    assert callable(template_endpoint)
    assert template_endpoint()["total"] == 9
