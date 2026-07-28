"""FastAPI routes for the TikTok Lead Management Center."""

from __future__ import annotations

from typing import Any

from ..models import (
    Activity,
    Assignment,
    ConsentRecord,
    FollowUp,
    Handoff,
    Lead,
    LeadScope,
    LeadStatus,
    Qualification,
)
from ..service import TikTokLeadManagementCenter

ROUTES = (
    "/tiktok/leads",
    "/tiktok/leads/sources",
    "/tiktok/leads/imports",
    "/tiktok/leads/duplicates",
    "/tiktok/leads/qualification",
    "/tiktok/leads/scoring",
    "/tiktok/leads/segments",
    "/tiktok/leads/assignments",
    "/tiktok/leads/consent",
    "/tiktok/leads/activities",
    "/tiktok/leads/followups",
    "/tiktok/leads/handoffs",
    "/tiktok/leads/history",
    "/tiktok/leads/analytics",
)
TAG = ["tiktok-leads"]


def _scope() -> LeadScope:
    return LeadScope("default", "default", "api", frozenset({"tiktok:leads:admin"}))


def register_lead_routes(app: Any, service: TikTokLeadManagementCenter) -> None:
    def list_leads() -> list[Lead]:
        return service.scoped_values(service.leads.values(), _scope())

    def create_lead(item: Lead) -> Lead:
        return service.create_lead(item, _scope())

    def update_lead(lead_id: str, changes: dict[str, Any]) -> Lead:
        return service.update_lead(lead_id, changes, _scope())

    def transition(lead_id: str, status: LeadStatus) -> Lead:
        return service.transition(lead_id, status, _scope())

    def import_records(request: dict[str, Any]) -> dict[str, Any]:
        return service.import_records(
            str(request["id"]),
            str(request["payload"]),
            str(request["format"]),
            dict(request["mapping"]),
            _scope(),
            dry_run=bool(request.get("dry_run", True)),
            maximum_rows=int(request.get("maximum_rows", 1000)),
        )

    def propose_merge(request: dict[str, str]) -> dict[str, Any]:
        return service.propose_merge(
            request["primary_id"], request["duplicate_id"], _scope()
        )

    def qualify(item: Qualification) -> Qualification:
        return service.qualify(item, _scope())

    def score(lead_id: str, factors: dict[str, Any]) -> Any:
        return service.score(lead_id, _scope(), **factors)

    def add_segment(request: dict[str, Any]) -> dict[str, Any]:
        return service.add_segment(
            str(request["id"]),
            str(request["kind"]),
            list(request["lead_ids"]),
            _scope(),
        )

    def assign(item: Assignment) -> Assignment:
        return service.assign(item, _scope())

    def consent(item: ConsentRecord) -> ConsentRecord:
        return service.record_consent(item, _scope())

    def activity(item: Activity) -> Activity:
        return service.add_activity(item, _scope())

    def followup(item: FollowUp) -> FollowUp:
        return service.plan_followup(item, _scope())

    def handoff(item: Handoff) -> Handoff:
        return service.handoff(item, _scope())

    app.add_api_route(ROUTES[0], list_leads, methods=["GET"], tags=TAG)
    app.add_api_route(ROUTES[0], create_lead, methods=["POST"], tags=TAG)
    app.add_api_route(
        f"{ROUTES[0]}/{{lead_id}}", update_lead, methods=["PATCH"], tags=TAG
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{lead_id}}/transition",
        transition,
        methods=["POST"],
        tags=TAG,
    )
    collections = (
        service.sources,
        service.imports,
        service.duplicates,
        service.qualifications,
        service.scores,
        service.segments,
        service.assignments,
        service.consents,
        service.activities,
        service.followups,
        service.handoffs,
    )
    for path, collection in zip(ROUTES[1:12], collections, strict=True):
        app.add_api_route(
            path,
            _collection_reader(collection),
            methods=["GET"],
            tags=TAG,
        )
    creators = (
        (ROUTES[2], import_records),
        (ROUTES[3], propose_merge),
        (ROUTES[4], qualify),
        (f"{ROUTES[5]}/{{lead_id}}", score),
        (ROUTES[6], add_segment),
        (ROUTES[7], assign),
        (ROUTES[8], consent),
        (ROUTES[9], activity),
        (ROUTES[10], followup),
        (ROUTES[11], handoff),
    )
    for path, creator in creators:
        app.add_api_route(path, creator, methods=["POST"], tags=TAG)
    app.add_api_route(
        ROUTES[12], lambda: service.history(_scope()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        ROUTES[13], lambda: service.analytics(_scope()), methods=["GET"], tags=TAG
    )
    app.add_api_route(
        "/tiktok/leads/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=TAG,
    )
    app.add_api_route(
        "/tiktok/leads/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=TAG,
    )


def _collection_reader(collection: Any) -> Any:
    def read() -> list[Any]:
        scope = _scope()
        return [
            item
            for item in collection.values()
            if (item.get("tenant") if isinstance(item, dict) else item.tenant)
            == scope.tenant
            and (
                item.get("workspace") if isinstance(item, dict) else item.workspace
            )
            == scope.workspace
        ]

    return read


API_MODELS = (
    Activity,
    Assignment,
    ConsentRecord,
    FollowUp,
    Handoff,
    Lead,
    LeadStatus,
    Qualification,
)
