"""Bounded, read-only integration ports."""

from __future__ import annotations

from typing import Any, Protocol

from .models import MAX_RESULTS, RequestScope, TimeRange

INTEGRATION_MODULES = (
    "growth_center", "content_pipeline", "campaign_center", "creator_workspace",
    "optimization_center", "decision_center", "control_tower", "recovery_center",
    "execution_engine", "operations_planner", "automation_engine", "runtime_manager",
    "resource_center", "task_scheduler", "browser_cluster", "device_center",
    "account_center", "browser_runtime", "proxy_center", "workflow_center",
    "operations_center", "risk_control", "content_center", "publishing_center",
    "data_collection", "interaction_center", "analytics_center", "local_runtime",
)


class ReadOnlyPerformancePort(Protocol):
    def snapshot(
        self, module: str, scope: RequestScope, time_range: TimeRange, limit: int
    ) -> dict[str, Any]: ...


class BoundedTestDouble:
    """Offline adapter that cannot mutate upstream modules."""

    def snapshot(
        self, module: str, scope: RequestScope, time_range: TimeRange, limit: int
    ) -> dict[str, Any]:
        time_range.validate()
        if module not in INTEGRATION_MODULES:
            raise ValueError("Unsupported analytical source module.")
        if not 1 <= limit <= MAX_RESULTS:
            raise ValueError("Result limit must be within [1, 500].")
        return {
            "module": module,
            "tenant": scope.tenant,
            "workspace": scope.workspace,
            "read_only": True,
            "limit": limit,
            "records": [],
        }
