"""HTTP API for advisory TikTok decisions."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..models import DecisionScope
from ..service import TikTokAIIntelligentDecisionCenter

ROUTES = (
    "/tiktok/decision-center/decisions",
    "/tiktok/decision-center/evaluations",
    "/tiktok/decision-center/recommendations",
    "/tiktok/decision-center/approvals",
    "/tiktok/decision-center/history",
    "/tiktok/decision-center/analytics",
)


def register_decision_center_routes(
    app: Any, service: TikTokAIIntelligentDecisionCenter
) -> None:
    """Register read-only review endpoints; mutation stays in bounded services."""

    def scope() -> DecisionScope:
        return DecisionScope(
            "default",
            "default",
            "api",
            frozenset({"tiktok:decision:admin"}),
        )

    readers = {
        ROUTES[0]: lambda: [
            item.to_dict()
            for item in service.scoped(service.decisions.values(), scope())
        ],
        ROUTES[1]: lambda: [
            asdict(item)
            for item in service.scoped(service.evaluations.values(), scope())
        ],
        ROUTES[2]: lambda: [
            asdict(item)
            for item in service.scoped(service.recommendations.values(), scope())
        ],
        ROUTES[3]: lambda: [
            asdict(item) for item in service.scoped(service.approvals.values(), scope())
        ],
        ROUTES[4]: lambda: [
            asdict(item) for item in service.scoped(service.history, scope())
        ],
        ROUTES[5]: lambda: service.analytics(scope()),
        "/tiktok/decision-center/evidence": lambda: [
            asdict(item) for item in service.scoped(service.evidence.values(), scope())
        ],
        "/tiktok/decision-center/dashboard": lambda: service.dashboard(scope()),
        "/tiktok/decision-center/metrics": service.metrics.render_prometheus,
    }
    for path, endpoint in readers.items():
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-decision-center"]
        )
