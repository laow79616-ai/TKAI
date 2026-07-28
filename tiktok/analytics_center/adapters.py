"""Read-only ports for TikTok modules and shared analytics infrastructure."""

from __future__ import annotations

from typing import Protocol

from .models import AnalyticsScope


class AnalyticsModulePort(Protocol):
    def metrics(self, scope: AnalyticsScope) -> dict[str, float]: ...


class NullAnalyticsModulePort:
    """Mock-safe adapter with no live TikTok dependency."""

    def metrics(self, scope: AnalyticsScope) -> dict[str, float]:
        return {}


MODULES = (
    "accounts",
    "browsers",
    "proxies",
    "farming",
    "content",
    "publishing",
    "collection",
    "interaction",
    "risk",
    "workflow",
    "operations",
)
