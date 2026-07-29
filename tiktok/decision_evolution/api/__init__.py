"""Read-only API for the TikTok Decision Evolution Center."""

from __future__ import annotations

from typing import Any

from ..models import DecisionEvolutionContext
from ..service import TikTokDecisionEvolutionCenter

RESOURCE_NAMES = (
    "profiles",
    "decisions",
    "outcomes",
    "baselines",
    "patterns",
    "comparisons",
    "evaluations",
    "confidence",
    "lessons",
    "recommendations",
    "reviews",
    "versions",
)
ROUTES = tuple(
    f"/tiktok/decision-evolution/{resource}" for resource in RESOURCE_NAMES
) + (
    "/tiktok/decision-evolution/history",
    "/tiktok/decision-evolution/analytics",
)


def register_decision_evolution_routes(
    app: Any, service: TikTokDecisionEvolutionCenter
) -> None:
    def context() -> DecisionEvolutionContext:
        return DecisionEvolutionContext(
            "default",
            "default",
            "api",
            frozenset({"tiktok:decision-evolution:read"}),
        )

    for name in RESOURCE_NAMES:
        store = getattr(service, name)

        def endpoint(
            store: dict[str, object] = store,
        ) -> list[dict[str, object]]:
            return service.items(store, context())

        app.add_api_route(
            f"/tiktok/decision-evolution/{name}",
            endpoint,
            methods=["GET"],
            tags=["tiktok-decision-evolution"],
        )
    app.add_api_route(
        "/tiktok/decision-evolution/history",
        lambda: service.get_history(context()),
        methods=["GET"],
        tags=["tiktok-decision-evolution"],
    )
    app.add_api_route(
        "/tiktok/decision-evolution/analytics",
        lambda: service.analytics(context()),
        methods=["GET"],
        tags=["tiktok-decision-evolution"],
    )
    app.add_api_route(
        "/tiktok/decision-evolution/dashboard",
        lambda: service.dashboard(context()),
        methods=["GET"],
        tags=["tiktok-decision-evolution"],
    )
    app.add_api_route(
        "/tiktok/decision-evolution/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-decision-evolution"],
    )
