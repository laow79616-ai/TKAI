"""HTTP registration for the Enterprise TikTok Campaign Center."""

from __future__ import annotations

from typing import Any

from ..models import (
    Campaign,
    CampaignApproval,
    CampaignPlan,
    CampaignSchedule,
    CampaignScope,
    CampaignStatus,
)
from ..service import TikTokCampaignCenter

ROUTES = (
    "/tiktok/campaigns",
    "/tiktok/campaigns/plans",
    "/tiktok/campaigns/schedules",
    "/tiktok/campaigns/monitoring",
    "/tiktok/campaigns/analytics",
)


def _scope() -> CampaignScope:
    return CampaignScope(
        "default", "default", "api", frozenset({"tiktok:campaign:admin"})
    )


def register_campaign_routes(app: Any, service: TikTokCampaignCenter) -> None:
    def create_campaign(campaign: Campaign) -> Campaign:
        return service.create(campaign, _scope())

    def update_campaign(campaign_id: str, changes: dict[str, Any]) -> Campaign:
        return service.update(campaign_id, changes, _scope())

    def create_plan(plan: CampaignPlan) -> CampaignPlan:
        return service.add_plan(plan, _scope())

    def create_schedule(schedule: CampaignSchedule) -> CampaignSchedule:
        return service.add_schedule(schedule, _scope())

    def decide_approval(approval: CampaignApproval) -> CampaignApproval:
        return service.decide_approval(approval, _scope())

    def transition_campaign(campaign_id: str, target: CampaignStatus) -> Campaign:
        return service.transition(campaign_id, target, _scope())

    app.add_api_route(
        ROUTES[0],
        lambda: service.list(_scope()),
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        ROUTES[0],
        create_campaign,
        methods=["POST"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/approvals",
        lambda: [
            item
            for item in service.approvals.values()
            if item.tenant == _scope().tenant and item.workspace == _scope().workspace
        ],
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/approvals",
        decide_approval,
        methods=["POST"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{campaign_id}}",
        lambda campaign_id: service.get(campaign_id, _scope()),
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{campaign_id}}",
        update_campaign,
        methods=["PATCH"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{campaign_id}}",
        lambda campaign_id: service.delete(campaign_id, _scope()),
        methods=["DELETE"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{campaign_id}}/transition",
        transition_campaign,
        methods=["POST"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        ROUTES[1],
        lambda: [
            item
            for item in service.plans.values()
            if item.tenant == _scope().tenant and item.workspace == _scope().workspace
        ],
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        ROUTES[1],
        create_plan,
        methods=["POST"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        ROUTES[2],
        lambda: [
            item
            for item in service.schedules.values()
            if item.tenant == _scope().tenant and item.workspace == _scope().workspace
        ],
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        ROUTES[2],
        create_schedule,
        methods=["POST"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        ROUTES[3],
        lambda: [
            service.monitoring(item.id, _scope()) for item in service.list(_scope())
        ],
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[3]}/{{campaign_id}}",
        lambda campaign_id: service.monitoring(campaign_id, _scope()),
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        ROUTES[4],
        lambda: [
            service.analytics(item.id, _scope()) for item in service.list(_scope())
        ],
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[4]}/{{campaign_id}}",
        lambda campaign_id: service.analytics(campaign_id, _scope()),
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )
    app.add_api_route(
        f"{ROUTES[0]}/{{campaign_id}}/history",
        lambda campaign_id: service.history(campaign_id, _scope()),
        methods=["GET"],
        tags=["tiktok-campaign-center"],
    )


__all__ = [
    "Campaign",
    "CampaignPlan",
    "CampaignSchedule",
    "ROUTES",
    "register_campaign_routes",
]
