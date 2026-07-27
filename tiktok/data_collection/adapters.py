"""Bounded ports that reuse existing TKAI platform services."""

from __future__ import annotations

from typing import Any, Protocol

from .models import CollectionFilter, CollectionSource


class AccountCenterPort(Protocol):
    def validate(self, reference: str, tenant: str, workspace: str) -> bool: ...


class BrowserRuntimePort(Protocol):
    def collect(
        self,
        source: CollectionSource,
        filters: CollectionFilter,
        tenant: str,
        workspace: str,
    ) -> list[dict[str, Any]]: ...


class ProxyCenterPort(Protocol):
    def healthy_for(self, account: str, tenant: str, workspace: str) -> bool: ...


class WorkflowPort(Protocol):
    def checkpoint(self, pipeline: str, stage: str, scope: str) -> str: ...


class AutomationPort(Protocol):
    def schedule(self, task: str, schedule: str, scope: str) -> bool: ...


class NullAccountCenterPort:
    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference and tenant and workspace)


class NullBrowserRuntimePort:
    """Mock-only collector. It never accesses TikTok or a network."""

    def collect(
        self,
        source: CollectionSource,
        filters: CollectionFilter,
        tenant: str,
        workspace: str,
    ) -> list[dict[str, Any]]:
        if not all((source.id, tenant, workspace)):
            return []
        return [{"source_reference": source.id, "collected_by": "mock-runtime"}]


class NullProxyCenterPort:
    def healthy_for(self, account: str, tenant: str, workspace: str) -> bool:
        return bool(account and tenant and workspace)


class NullWorkflowPort:
    def checkpoint(self, pipeline: str, stage: str, scope: str) -> str:
        return f"checkpoint://{scope}/{pipeline}/{stage}"


class NullAutomationPort:
    def schedule(self, task: str, schedule: str, scope: str) -> bool:
        return bool(task and schedule and scope)


class ExistingAccountCenterAdapter:
    def __init__(self, center: Any) -> None:
        self.center = center

    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        account = getattr(self.center, "accounts", {}).get(reference)
        return bool(
            account and account.tenant == tenant and account.workspace == workspace
        )


class ExistingProxyCenterAdapter:
    def __init__(self, center: Any) -> None:
        self.center = center

    def healthy_for(self, account: str, tenant: str, workspace: str) -> bool:
        allocations = getattr(self.center, "allocations", {}).values()
        return any(
            allocation.tenant == tenant
            and allocation.workspace == workspace
            and allocation.target_reference == account
            for allocation in allocations
        ) or not getattr(self.center, "allocations", {})
