"""Read-only bounded adapters for existing TikTok decision inputs."""

from __future__ import annotations

from hashlib import sha256
from typing import Any, Protocol

from tiktok.control_tower import ControlTowerScope, TikTokAIControlTower

from .models import DECISION_INPUTS, DecisionScope

INPUT_MODULES = {
    "account_state": "accounts",
    "browser_cluster_state": "browser_cluster",
    "device_state": "devices",
    "proxy_state": "proxies",
    "runtime_state": "runtime",
    "workflow_state": "workflows",
    "automation_state": "automation",
    "execution_state": "execution",
    "recovery_state": "recovery",
    "risk_state": "risk",
    "analytics_kpis": "analytics",
    "resource_utilization": "resources",
}


class DecisionInputProvider(Protocol):
    read_only: bool

    def collect(self, scope: DecisionScope) -> dict[str, dict[str, Any]]: ...


class ReferenceVault(Protocol):
    def protect(self, value: str, scope: DecisionScope) -> str: ...


class LocalReferenceVault:
    def __init__(self, key: bytes = b"tkai-decision-reference-v1") -> None:
        self._key = key

    def protect(self, value: str, scope: DecisionScope) -> str:
        digest = sha256(
            self._key
            + scope.tenant.encode()
            + scope.workspace.encode()
            + value.encode()
        ).hexdigest()
        return f"sealed-ref://{digest}"


class ControlTowerDecisionInputAdapter:
    """Maps Control Tower projections into bounded decision context."""

    read_only = True

    def __init__(self, tower: TikTokAIControlTower) -> None:
        self.tower = tower

    def collect(self, scope: DecisionScope) -> dict[str, dict[str, Any]]:
        tower_scope = ControlTowerScope(
            scope.tenant,
            scope.workspace,
            scope.actor,
            frozenset({"tiktok:control-tower:read"}),
        )
        snapshots = self.tower.collect(tower_scope)
        return {
            name: snapshots[module].to_dict() for name, module in INPUT_MODULES.items()
        }


class MockDecisionInputProvider:
    """Deterministic offline input provider for tests."""

    read_only = True

    def collect(self, scope: DecisionScope) -> dict[str, dict[str, Any]]:
        return {
            name: {
                "health": "healthy",
                "status": "operational",
                "score": 0.8,
                "source": f"mock://{name}",
            }
            for name in DECISION_INPUTS
        }
