"""FastAPI registration for customer journeys."""

from __future__ import annotations

from typing import Any

from ..models import JourneyScope
from ..service import TikTokCustomerJourneyCenter

ROUTES = (
    "/tiktok/customer-journeys",
    "/tiktok/customer-journeys/stages",
    "/tiktok/customer-journeys/touchpoints",
    "/tiktok/customer-journeys/conversions",
    "/tiktok/customer-journeys/recommendations",
    "/tiktok/customer-journeys/analytics",
)
TAG = ["tiktok-customer-journeys"]


def _scope() -> JourneyScope:
    return JourneyScope(
        "default",
        "default",
        "api",
        frozenset({"tiktok:customer-journeys:admin"}),
    )


def _reader(service: TikTokCustomerJourneyCenter, collection: Any) -> Any:
    def read() -> list[Any]:
        return service.scoped_values(collection.values(), _scope())

    return read


def _creator(function: Any) -> Any:
    def create(item: Any) -> Any:
        return function(item, _scope())

    return create


def register_customer_journey_routes(
    app: Any, service: TikTokCustomerJourneyCenter
) -> None:
    app.add_api_route(
        ROUTES[0],
        lambda: service.scoped_values(service.journeys.values(), _scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[0],
        lambda item: service.create_journey(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[1],
        lambda: service.history(_scope())["stages"],
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[1],
        lambda journey_id, status, stage, custom_stage="": service.transition(
            journey_id, status, stage, _scope(), custom_stage=custom_stage
        ),
        methods=["POST"],
        tags=TAG,
    )
    for path, collection, creator in (
        (ROUTES[2], service.touchpoints, service.add_touchpoint),
        (ROUTES[3], service.conversions, service.record_conversion),
        (ROUTES[4], service.recommendations, service.recommend),
    ):
        app.add_api_route(
            path,
            _reader(service, collection),
            methods=["GET"],
            tags=TAG,
        )
        app.add_api_route(
            path,
            _creator(creator),
            methods=["POST"],
            tags=TAG,
        )
    app.add_api_route(
        "/tiktok/customer-journeys/milestones",
        lambda item: service.add_milestone(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/customer-journeys/segments",
        lambda item: service.add_segment(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/customer-journeys/handoffs",
        lambda item: service.handoff(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[5], lambda: service.analytics(_scope()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        "/tiktok/customer-journeys/history",
        lambda: service.history(_scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/customer-journeys/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/customer-journeys/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=TAG,
    )
