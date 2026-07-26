from app_store import EnterpriseAppStore
from app_store.api import register_app_store_routes


class App:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], object] = {}

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        for method in methods:
            self.routes[(method, path)] = endpoint


def test_app_store_api_contract() -> None:
    app = App()
    register_app_store_routes(app, EnterpriseAppStore())
    for path in (
        "/app-store",
        "/app-store/applications",
        "/app-store/publishers",
        "/app-store/packages",
        "/app-store/installations",
        "/app-store/updates",
        "/app-store/licenses",
        "/app-store/subscriptions",
        "/app-store/reviews",
        "/app-store/moderation",
    ):
        assert ("GET", path) in app.routes
    assert ("POST", "/app-store/applications") in app.routes
    assert ("POST", "/app-store/publishers") in app.routes
