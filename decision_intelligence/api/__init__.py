"""Framework-neutral Decision Intelligence API facade."""

from typing import Any

from ..platform import DecisionIntelligencePlatform, DecisionScope


class DecisionIntelligenceAPI:
    PREFIX = "/decision-intelligence"
    RESOURCES = (
        "decisions",
        "evaluations",
        "recommendations",
        "approvals",
        "simulations",
        "insights",
    )
    ROUTES = tuple(f"/decision-intelligence/{resource}" for resource in RESOURCES)

    def __init__(self, platform: DecisionIntelligencePlatform) -> None:
        self.platform = platform

    def get(self, path: str, scope: DecisionScope) -> Any:
        resource = path.removeprefix(f"{self.PREFIX}/")
        if resource not in self.RESOURCES:
            raise KeyError("Unknown Decision Intelligence API route.")
        return self.platform.dashboard(scope)[resource]


def register_decision_intelligence_routes(
    app: Any, platform: DecisionIntelligencePlatform
) -> None:
    """Register tenant-scoped read endpoints on a FastAPI-like application."""

    api = DecisionIntelligenceAPI(platform)
    for path in api.ROUTES:
        app.add_api_route(
            path,
            lambda tenant, workspace, actor, route=path: api.get(
                route, DecisionScope(tenant, workspace, actor)
            ),
            methods=["GET"],
            tags=["decision-intelligence"],
        )
