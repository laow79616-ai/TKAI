from knowledge_platform import KnowledgePlatform
from knowledge_platform.api import register_knowledge_routes


class App:
    def __init__(self) -> None:
        self.routes: dict[tuple[str, str], object] = {}

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        for method in methods:
            self.routes[(method, path)] = endpoint


def test_api_contract() -> None:
    app = App()
    register_knowledge_routes(app, KnowledgePlatform())
    for path in (
        "/knowledge-bases",
        "/collections",
        "/documents",
        "/ingestion",
        "/retrieval",
        "/citations",
        "/connectors",
        "/evaluation",
    ):
        assert ("GET", path) in app.routes
