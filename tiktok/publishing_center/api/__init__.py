"""HTTP route registration for the TikTok AI Publishing Center."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..models import PublishingScope
from ..service import TikTokPublishingCenter

ROUTES = (
    "/tiktok/publishing/jobs",
    "/tiktok/publishing/queue",
    "/tiktok/publishing/scheduler",
    "/tiktok/publishing/calendar",
    "/tiktok/publishing/approvals",
    "/tiktok/publishing/history",
    "/tiktok/publishing/analytics",
)


def _scope() -> PublishingScope:
    return PublishingScope(
        "default", "default", "api", frozenset({"tiktok:publishing:admin"})
    )


def register_publishing_center_routes(
    app: Any, service: TikTokPublishingCenter
) -> None:
    readers: dict[str, Callable[[], Any]] = {
        ROUTES[0]: lambda: [job.to_dict() for job in service.list_jobs(_scope())],
        ROUTES[1]: lambda: [job.to_dict() for job in service.queue(_scope())],
        ROUTES[2]: lambda: service.dashboard(_scope())["schedules"],
        ROUTES[3]: lambda: service.dashboard(_scope())["calendar"],
        ROUTES[4]: lambda: service.dashboard(_scope())["approvals"],
        ROUTES[5]: lambda: service.dashboard(_scope())["history"],
        ROUTES[6]: lambda: service.analytics(_scope()),
    }
    for path, endpoint in readers.items():
        app.add_api_route(path, endpoint, methods=["GET"], tags=["tiktok-publishing"])
    app.add_api_route(
        "/tiktok/publishing/dashboard",
        lambda: service.dashboard(_scope()),
        methods=["GET"],
        tags=["tiktok-publishing"],
    )
    app.add_api_route(
        "/tiktok/publishing/metrics",
        service.metrics.render_prometheus,
        methods=["GET"],
        tags=["tiktok-publishing"],
    )
