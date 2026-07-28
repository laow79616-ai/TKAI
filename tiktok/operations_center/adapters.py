"""Bounded ports for existing TikTok modules and shared infrastructure."""

from __future__ import annotations

from typing import Any, Protocol

from .models import OperationsScope


class OperationsModulePort(Protocol):
    def status(self, scope: OperationsScope) -> dict[str, Any]: ...

    def execute(
        self,
        action: str,
        resource_reference: str,
        scope: OperationsScope,
    ) -> dict[str, Any]: ...


class NullOperationsModulePort:
    """Safe test double: reports unknown health and accepts no external mutation."""

    def status(self, scope: OperationsScope) -> dict[str, Any]:
        return {"status": "unknown", "healthy": 0, "unhealthy": 0}

    def execute(
        self,
        action: str,
        resource_reference: str,
        scope: OperationsScope,
    ) -> dict[str, Any]:
        return {
            "accepted": True,
            "action": action,
            "resource_reference": resource_reference,
        }


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
    "workflows",
)
