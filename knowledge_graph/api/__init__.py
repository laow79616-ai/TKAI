"""Framework-neutral Enterprise AI Knowledge Graph API."""

from typing import Any

from ..platform import GraphScope, KnowledgeGraphPlatform


class KnowledgeGraphAPI:
    PREFIX = "/knowledge-graph"
    RESOURCES = (
        "graphs",
        "entities",
        "relationships",
        "ontology",
        "taxonomy",
        "queries",
        "lineage",
        "analytics",
    )
    ROUTES = tuple(f"/knowledge-graph/{resource}" for resource in RESOURCES)

    def __init__(self, platform: KnowledgeGraphPlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: GraphScope) -> Any:
        prefix = f"{self.PREFIX}/"
        if not path.startswith(prefix):
            raise KeyError("Unknown Knowledge Graph API route.")
        resource = path.removeprefix(prefix)
        if resource not in self.RESOURCES:
            raise KeyError("Unknown Knowledge Graph API route.")
        return self.platform.resource(resource, scope)


def register_knowledge_graph_routes(
    app: Any, platform: KnowledgeGraphPlatform
) -> None:
    api = KnowledgeGraphAPI(platform)
    for path in api.ROUTES:
        app.add_api_route(
            path,
            lambda tenant, workspace, actor, route=path: api.get(
                route, GraphScope(tenant, workspace, actor)
            ),
            methods=["GET"],
            tags=["knowledge-graph"],
        )
