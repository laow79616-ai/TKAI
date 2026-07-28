"""Declarative Device Center API bindings."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..models import DeviceScope
from ..service import TikTokDeviceCenter

BASE = "/tiktok/device-center"
ROUTES = tuple(
    [BASE]
    + [
        f"{BASE}/{resource}"
        for resource in (
            "devices",
            "groups",
            "profiles",
            "health",
            "recovery",
            "statistics",
        )
    ]
)


def register_device_center_routes(app: Any, center: TikTokDeviceCenter) -> None:
    def scoped(tenant: str, workspace: str, actor: str) -> DeviceScope:
        return DeviceScope(tenant, workspace, actor)

    def section(name: str) -> Callable[..., Any]:
        return lambda tenant, workspace, actor: center.dashboard(
            scoped(tenant, workspace, actor)
        )[name]

    handlers: dict[str, Callable[..., Any]] = {
        BASE: lambda tenant, workspace, actor: center.dashboard(
            scoped(tenant, workspace, actor)
        ),
        f"{BASE}/devices": section("devices"),
        f"{BASE}/groups": section("groups"),
        f"{BASE}/profiles": section("profiles"),
        f"{BASE}/health": lambda tenant, workspace, actor: center.health(
            scoped(tenant, workspace, actor)
        ),
        f"{BASE}/recovery": section("recovery"),
        f"{BASE}/statistics": lambda tenant, workspace, actor: center.statistics(
            scoped(tenant, workspace, actor)
        ),
    }
    for path, handler in handlers.items():
        try:
            app.add_api_route(
                path, handler, methods=["GET"], tags=["tiktok-device-center"]
            )
        except TypeError:
            app.add_api_route(path, handler, methods=["GET"])
