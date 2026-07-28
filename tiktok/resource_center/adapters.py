"""Bounded inventory ports for existing TikTok platform modules."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .models import Resource, ResourceScope


class InventoryPort(Protocol):
    def discover(self, scope: ResourceScope) -> Iterable[Resource]: ...


class EmptyInventoryPort:
    """Safe local default that never reaches TikTok or external services."""

    def discover(self, scope: ResourceScope) -> Iterable[Resource]:
        return ()


INTEGRATION_NAMES = frozenset(
    {
        "browser_cluster",
        "device_center",
        "task_scheduler",
        "browser_runtime",
        "account_center",
        "proxy_center",
        "workflow_center",
        "operations_center",
        "risk_control_center",
    }
)
