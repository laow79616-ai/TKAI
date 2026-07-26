"""Transport-neutral Enterprise Plugin Marketplace API."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..marketplace import EnterprisePluginMarketplace


class PluginApi:
    def __init__(self, marketplace: EnterprisePluginMarketplace) -> None:
        self.marketplace = marketplace

    def list_plugins(
        self, query: str = "", category: str = "", tag: str = ""
    ) -> dict[str, object]:
        records = self.marketplace.catalog.search(
            query, category=category, tag=tag
        )
        return {"data": [item.to_dict() for item in records], "total": len(records)}

    def install(self, payload: dict[str, object]) -> dict[str, object]:
        plugin_id = _required(payload, "id")
        version = payload.get("version")
        record = self.marketplace.install(
            plugin_id,
            str(version) if version is not None else None,
            str(payload.get("actor", "api")),
        )
        return record.to_dict()

    def uninstall(self, plugin_id: str) -> dict[str, object]:
        return self.marketplace.uninstall(plugin_id, "api").to_dict()

    def enable(self, payload: dict[str, object]) -> dict[str, object]:
        return self.marketplace.enable(_required(payload, "id"), "api").to_dict()

    def disable(self, payload: dict[str, object]) -> dict[str, object]:
        return self.marketplace.disable(_required(payload, "id"), "api").to_dict()

    def update(self, payload: dict[str, object]) -> dict[str, object]:
        plugin_id = _required(payload, "id")
        version = payload.get("version")
        return self.marketplace.upgrade(
            plugin_id,
            str(version) if version is not None else None,
            "api",
        ).to_dict()


def register_plugin_routes(
    app: Any, marketplace: EnterprisePluginMarketplace
) -> PluginApi:
    """Register the required routes on a FastAPI-compatible host."""
    bridge = PluginApi(marketplace)
    routes: tuple[tuple[str, Callable[..., object], tuple[str, ...]], ...] = (
        ("/plugins", bridge.list_plugins, ("GET",)),
        ("/plugins/install", bridge.install, ("POST",)),
        ("/plugins/{plugin_id}", bridge.uninstall, ("DELETE",)),
        ("/plugins/enable", bridge.enable, ("POST",)),
        ("/plugins/disable", bridge.disable, ("POST",)),
        ("/plugins/update", bridge.update, ("POST",)),
    )
    for path, endpoint, methods in routes:
        app.add_api_route(path, endpoint, methods=list(methods), tags=["plugins"])
    return bridge


def _required(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Plugin {key} is required")
    return value


__all__ = ("PluginApi", "register_plugin_routes")
