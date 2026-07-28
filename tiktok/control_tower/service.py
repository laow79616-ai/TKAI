"""Unified read-only operational cockpit for existing TikTok subsystems."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from .adapters import (
    ControlTowerProvider,
    ExistingModuleProvider,
    LocalReferenceVault,
    ReferenceVault,
)
from .metrics import ControlTowerMetrics
from .models import (
    CONTROL_TOWER_MODULES,
    DASHBOARD_SECTIONS,
    ActivityEvent,
    ControlTowerAlert,
    ControlTowerScope,
    HealthStatus,
    ModuleSnapshot,
)


class TikTokAIControlTower:
    """Aggregates existing module state without duplicating their infrastructure."""

    def __init__(
        self,
        provider: ControlTowerProvider | None = None,
        vault: ReferenceVault | None = None,
    ) -> None:
        self.provider = provider or ExistingModuleProvider()
        self.vault = vault or LocalReferenceVault()
        self.metrics = ControlTowerMetrics()
        self.alerts: list[ControlTowerAlert] = []
        self.activity: list[ActivityEvent] = []

    @staticmethod
    def _require(scope: ControlTowerScope, permission: str = "read") -> None:
        required = f"tiktok:control-tower:{permission}"
        if (
            required not in scope.permissions
            and "tiktok:control-tower:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: {required}")

    @staticmethod
    def _safe_detail(detail: str) -> None:
        forbidden = ("password=", "secret=", "token=", "cookie=", "session=")
        if any(marker in detail.casefold() for marker in forbidden):
            raise ValueError("Secrets are forbidden in Control Tower logs.")

    def record_activity(
        self, scope: ControlTowerScope, action: str, module: str, detail: str = ""
    ) -> None:
        self._require(scope, "audit")
        self._safe_detail(detail)
        self.activity.append(
            ActivityEvent(
                scope.tenant,
                scope.workspace,
                scope.actor,
                action,
                module,
                detail,
            )
        )

    def collect(self, scope: ControlTowerScope) -> dict[str, ModuleSnapshot]:
        self._require(scope)
        snapshots: dict[str, ModuleSnapshot] = {}
        total_latency = 0.0
        for module in CONTROL_TOWER_MODULES:
            started = perf_counter()
            payload = self.provider.snapshot(module, scope)
            latency = perf_counter() - started
            total_latency += latency
            health = HealthStatus(str(payload.get("health", "unavailable")))
            snapshot = ModuleSnapshot(
                module,
                scope.tenant,
                scope.workspace,
                health,
                str(payload.get("status", "unknown")),
                dict(payload.get("summary", {})),
                latency,
            )
            snapshots[module] = snapshot
        healthy = sum(
            item.health is HealthStatus.HEALTHY for item in snapshots.values()
        )
        self.metrics.set(
            "tiktok_control_tower_health", healthy / len(CONTROL_TOWER_MODULES)
        )
        self.metrics.set(
            "tiktok_control_tower_runtime",
            float(snapshots["runtime"].summary.get("active", 0)),
        )
        self.metrics.set(
            "tiktok_control_tower_resources",
            float(snapshots["resources"].summary.get("capacity_percent", 0)),
        )
        self.metrics.set("tiktok_control_tower_latency_seconds", total_latency)
        return snapshots

    def overview(self, scope: ControlTowerScope) -> dict[str, Any]:
        snapshots = self.collect(scope)
        counts = {
            status.value: sum(item.health is status for item in snapshots.values())
            for status in HealthStatus
        }
        global_health = (
            "healthy"
            if counts["healthy"] == len(snapshots)
            else "degraded"
            if counts["healthy"]
            else "unavailable"
        )
        return {
            "unified_overview": "TikTok AI Control Tower",
            "global_health": global_health,
            "platform_status": counts,
            "live_runtime": snapshots["runtime"].to_dict(),
            "resource_utilization": snapshots["resources"].to_dict(),
            "workflow_status": snapshots["workflows"].to_dict(),
            "execution_status": snapshots["execution"].to_dict(),
            "automation_status": snapshots["automation"].to_dict(),
            "risk_status": snapshots["risk"].to_dict(),
            "recovery_status": snapshots["recovery"].to_dict(),
            "analytics_summary": snapshots["analytics"].to_dict(),
        }

    def module(self, name: str, scope: ControlTowerScope) -> dict[str, Any]:
        if name not in CONTROL_TOWER_MODULES:
            raise ValueError(f"Unknown Control Tower module: {name}")
        return self.collect(scope)[name].to_dict()

    def topology(self, scope: ControlTowerScope) -> dict[str, Any]:
        snapshots = self.collect(scope)
        return {
            "root": "tiktok-ai-control-tower",
            "nodes": [item.to_dict() for item in snapshots.values()],
            "edges": [
                {"from": "tiktok-ai-control-tower", "to": module, "mode": "read-only"}
                for module in CONTROL_TOWER_MODULES
            ],
        }

    def create_alert(
        self,
        scope: ControlTowerScope,
        module: str,
        severity: str,
        message: str,
        source_reference: str,
    ) -> ControlTowerAlert:
        self._require(scope, "alert")
        self._safe_detail(message)
        if module not in CONTROL_TOWER_MODULES:
            raise ValueError("Alert module is outside the TikTok Control Tower.")
        if severity not in {"info", "warning", "critical"}:
            raise ValueError("Unsupported alert severity.")
        alert = ControlTowerAlert(
            f"alert-{len(self.alerts) + 1}",
            scope.tenant,
            scope.workspace,
            module,
            severity,
            message,
            self.vault.protect(source_reference, scope),
        )
        self.alerts.append(alert)
        self.metrics.set(
            "tiktok_control_tower_alerts",
            float(len(self.scoped_alerts(scope))),
        )
        return alert

    def scoped_alerts(self, scope: ControlTowerScope) -> list[ControlTowerAlert]:
        self._require(scope)
        return [
            item
            for item in self.alerts
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def scoped_activity(self, scope: ControlTowerScope) -> list[ActivityEvent]:
        self._require(scope)
        return [
            item
            for item in self.activity
            if item.tenant == scope.tenant and item.workspace == scope.workspace
        ]

    def dashboard(self, scope: ControlTowerScope) -> dict[str, Any]:
        return {
            "sections": list(DASHBOARD_SECTIONS),
            "overview": self.overview(scope),
            "topology": self.topology(scope),
            "alerts": len(self.scoped_alerts(scope)),
            "activity": len(self.scoped_activity(scope)),
        }
