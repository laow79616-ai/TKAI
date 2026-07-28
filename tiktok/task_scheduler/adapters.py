"""Reference-only ports for existing TikTok and shared platform infrastructure."""

from __future__ import annotations

from typing import Any, Protocol

from .models import ScheduledTask, SchedulerScope, TaskType


class SchedulerPort(Protocol):
    def preflight(self, task: ScheduledTask, scope: SchedulerScope) -> None: ...
    def execute(self, task: ScheduledTask, scope: SchedulerScope) -> dict[str, Any]: ...


class BoundedTestPort:
    """Deterministic local adapter; it never connects to TikTok."""

    def preflight(self, task: ScheduledTask, scope: SchedulerScope) -> None:
        return None

    def execute(self, task: ScheduledTask, scope: SchedulerScope) -> dict[str, Any]:
        return {"reference": f"test-double://{task.id}", "bounded": True}


TASK_MODULE = {
    TaskType.ACCOUNT_HEALTH_CHECK: "accounts",
    TaskType.BROWSER_LAUNCH: "browser_runtime",
    TaskType.BROWSER_RECOVERY: "browser_cluster",
    TaskType.DEVICE_ALLOCATION: "devices",
    TaskType.DEVICE_RECOVERY: "devices",
    TaskType.PROXY_HEALTH_CHECK: "proxies",
    TaskType.PROXY_ALLOCATION: "proxies",
    TaskType.WORKFLOW_EXECUTION: "workflows",
    TaskType.PUBLISHING_JOB: "publishing",
    TaskType.COLLECTION_JOB: "collection",
    TaskType.INTERACTION_TASK: "interaction",
    TaskType.RISK_EVALUATION: "risk",
    TaskType.ANALYTICS_AGGREGATION: "analytics",
    TaskType.BACKUP: "local_runtime",
    TaskType.DIAGNOSTICS: "operations",
    TaskType.CUSTOM_BOUNDED: "custom",
}

MODULES = frozenset(TASK_MODULE.values())
