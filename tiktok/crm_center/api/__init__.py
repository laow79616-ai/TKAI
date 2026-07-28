"""FastAPI routes for the TikTok CRM Center."""

from __future__ import annotations

from typing import Any

from ..models import (
    Activity,
    ConsentRecord,
    Contact,
    CRMRecord,
    CRMScope,
    CRMStatus,
    FollowUp,
    Opportunity,
    Organization,
    Relationship,
)
from ..service import TikTokCRMCenter

ROUTES = (
    "/tiktok/crm/organizations",
    "/tiktok/crm/contacts",
    "/tiktok/crm/opportunities",
    "/tiktok/crm/activities",
    "/tiktok/crm/followups",
    "/tiktok/crm/analytics",
)
TAG = ["tiktok-crm"]


def _scope() -> CRMScope:
    return CRMScope("default", "default", "api", frozenset({"tiktok:crm:admin"}))


def _reader(service: TikTokCRMCenter, name: str) -> Any:
    def read() -> list[Any]:
        return service.scoped_values(getattr(service, name).values(), _scope())

    return read


def _creator(function: Any) -> Any:
    def create(item: Any) -> Any:
        return function(item, _scope())

    return create


def register_crm_routes(app: Any, service: TikTokCRMCenter) -> None:
    app.add_api_route(
        "/tiktok/crm", _reader(service, "records"), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        "/tiktok/crm",
        lambda item: service.create_record(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/crm/{crm_id}/transition",
        lambda crm_id, status: service.transition(crm_id, status, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    collections = (
        "organizations",
        "contacts",
        "opportunities",
        "activities",
        "followups",
    )
    creators = (
        service.add_organization,
        service.add_contact,
        service.add_opportunity,
        service.add_activity,
        service.propose_followup,
    )
    for path, collection, creator in zip(
        ROUTES[:5], collections, creators, strict=True
    ):
        app.add_api_route(path, _reader(service, collection), methods=["GET"], tags=TAG)
        app.add_api_route(path, _creator(creator), methods=["POST"], tags=TAG)
    app.add_api_route(
        "/tiktok/crm/relationships",
        _reader(service, "relationships"),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/crm/relationships",
        lambda item: service.add_relationship(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/crm/consent", _reader(service, "consents"), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        "/tiktok/crm/consent",
        lambda item: service.record_consent(item, _scope()),
        methods=["POST"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/crm/history",
        lambda: service.history(_scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        ROUTES[5], lambda: service.analytics(_scope()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        "/tiktok/crm/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/crm/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=TAG,
    )


API_MODELS = (
    Activity,
    ConsentRecord,
    Contact,
    CRMRecord,
    CRMScope,
    CRMStatus,
    FollowUp,
    Opportunity,
    Organization,
    Relationship,
)
