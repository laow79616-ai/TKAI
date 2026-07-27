from pathlib import Path

import pytest

from knowledge_graph import (
    METRICS,
    GraphScope,
    KnowledgeGraphAPI,
    KnowledgeGraphMetrics,
    KnowledgeGraphPlatform,
)


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, object]] = []

    def add_api_route(
        self, path: str, endpoint: object, *, methods: list[str], tags: list[str]
    ) -> None:
        self.routes.append((path, endpoint))


def test_api_registration_structure_docs_metrics_and_frontends() -> None:
    platform = KnowledgeGraphPlatform()
    api = KnowledgeGraphAPI(platform)
    scope = GraphScope("tenant", "workspace", "actor")
    assert len(api.ROUTES) == 8
    assert api.get("/knowledge-graph/graphs", scope) == []
    with pytest.raises(KeyError):
        api.get("/knowledge-graph/unknown", scope)
    app = FakeApp()
    from knowledge_graph import register_knowledge_graph_routes

    register_knowledge_graph_routes(app, platform)
    assert [path for path, _ in app.routes] == list(api.ROUTES)
    root = Path(__file__).parents[2]
    for module in (
        "graphs", "entities", "relationships", "ontologies", "taxonomies",
        "schemas", "properties", "reasoning", "traversal", "queries", "lineage",
        "provenance", "indexing", "analytics", "dashboard", "api",
    ):
        assert (root / "knowledge_graph" / module / "__init__.py").is_file()
    for document in (
        "Architecture", "Ontology", "Taxonomy", "Schema", "Entities",
        "Relationships", "Reasoning", "Traversal", "Queries", "Lineage",
        "Analytics", "Security", "Operations",
    ):
        assert (root / "docs" / "knowledge_graph" / f"{document}.md").is_file()
    assert len(METRICS) == 8
    assert "knowledge_graphs_total 0" in KnowledgeGraphMetrics().render_prometheus()
    dashboard = (root / "dashboard/frontend/src/App.tsx").read_text("utf-8")
    studio = (root / "studio/frontend/src/pages.ts").read_text("utf-8")
    server = (root / "server/api/app.py").read_text("utf-8")
    assert "KnowledgeGraphPage" in dashboard
    assert '"knowledge-graph"' in studio
    assert "register_knowledge_graph_routes" in server
