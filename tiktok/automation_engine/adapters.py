"""Bounded ports into existing TikTok modules and shared infrastructure."""

from __future__ import annotations

from typing import Any, Protocol

from .models import AutomationScope


class AutomationPort(Protocol):
    def health(self, module: str, scope: AutomationScope) -> dict[str, Any]: ...
    def execute(
        self,
        module: str,
        action: str,
        payload: dict[str, Any],
        scope: AutomationScope,
    ) -> dict[str, Any]: ...
    def rollback(
        self,
        module: str,
        action: str,
        payload: dict[str, Any],
        scope: AutomationScope,
    ) -> None: ...


class LocalMockPort:
    """Offline-safe default. Production hosts inject existing module adapters."""

    def health(self, module: str, scope: AutomationScope) -> dict[str, Any]:
        return {"healthy": True, "restriction_unresolved": False}

    def execute(
        self,
        module: str,
        action: str,
        payload: dict[str, Any],
        scope: AutomationScope,
    ) -> dict[str, Any]:
        return {"module": module, "action": action, "status": "accepted"}

    def rollback(
        self,
        module: str,
        action: str,
        payload: dict[str, Any],
        scope: AutomationScope,
    ) -> None:
        return None
