"""Read-only bounded adapters; governance never executes work."""

from __future__ import annotations

from typing import Protocol

from .models import AccessContext

INTEGRATION_MODULES = (
    "strategy_center",
    "mission_engine",
    "autonomous_operation",
    "decision_center",
    "optimization_center",
    "operations_planner",
    "automation_engine",
    "execution_engine",
    "recovery_center",
    "workflow_center",
    "task_scheduler",
    "runtime_manager",
    "resource_center",
    "browser_cluster",
    "device_center",
    "proxy_center",
    "publishing_center",
    "data_collection",
    "interaction_center",
    "risk_control",
    "operations_center",
    "control_tower",
    "business_workspace",
    "lead_center",
    "crm_center",
    "customer_journey_center",
    "business_intelligence_center",
    "performance_insights",
    "analytics_center",
    "local_runtime",
)


class GovernancePort(Protocol):
    def governance_snapshot(
        self, resource_id: str, context: AccessContext
    ) -> dict[str, object]: ...


class ReferenceOnlyGovernancePort:
    def __init__(self, module: str, service: object | None = None) -> None:
        self.module = module
        self.service = service

    def governance_snapshot(
        self, resource_id: str, context: AccessContext
    ) -> dict[str, object]:
        return {
            "module": self.module,
            "resource_id": resource_id,
            "tenant": context.tenant,
            "workspace": context.workspace,
            "governed": True,
            "operational_actions": False,
        }
