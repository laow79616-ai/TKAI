"""Read-only governance API surface."""
# ruff: noqa: E731, B905

from typing import Any

from ..models import AccessContext
from ..service import TikTokAutonomousGovernanceCenter

RESOURCES = (
    "profiles",
    "policies",
    "rules",
    "controls",
    "approvals",
    "reviews",
    "exceptions",
    "evidence",
    "audits",
    "changes",
    "versions",
    "risk",
    "compliance",
    "safety",
    "monitoring",
    "history",
    "analytics",
)
ROUTES = tuple(f"/tiktok/governance-center/{r}" for r in RESOURCES)


def register_governance_center_routes(
    app: Any, service: TikTokAutonomousGovernanceCenter
) -> None:
    def scope() -> AccessContext:
        return AccessContext(
            "default", "default", "api", frozenset({"tiktok:governance-center:admin"})
        )

    stores = {
        "profiles": service.profiles,
        "policies": service.policies,
        "rules": service.rules,
        "controls": service.controls,
        "approvals": service.approvals,
        "reviews": service.reviews,
        "exceptions": service.exceptions,
        "evidence": service.evidence,
        "changes": service.changes,
        "risk": service.risks,
    }
    for resource, path in zip(RESOURCES, ROUTES):
        if resource == "monitoring":
            endpoint = lambda: service.monitoring(scope())
        elif resource == "analytics":
            endpoint = lambda: service.analytics(scope())
        elif resource == "history":
            endpoint = lambda: service.history
        elif resource == "audits":
            endpoint = lambda: service.audits
        else:
            store = stores.get(resource, {})
            endpoint = lambda store=store: service._items(store, scope())
        app.add_api_route(
            path, endpoint, methods=["GET"], tags=["tiktok-governance-center"]
        )
    app.add_api_route(
        "/tiktok/governance-center/dashboard",
        lambda: service.dashboard(scope()),
        methods=["GET"],
        tags=["tiktok-governance-center"],
    )
    app.add_api_route(
        "/tiktok/governance-center/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-governance-center"],
    )
