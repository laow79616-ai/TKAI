"""Bounded ports that reuse existing TikTok platform infrastructure."""

from __future__ import annotations

from typing import Any, Protocol


class AccountCenterPort(Protocol):
    def validate(self, reference: str, tenant: str, workspace: str) -> bool: ...


class BrowserRuntimePort(Protocol):
    def publish(
        self, account: str, payload: dict[str, Any], tenant: str, workspace: str
    ) -> bool: ...


class ProxyCenterPort(Protocol):
    def healthy_for(self, account: str, tenant: str, workspace: str) -> bool: ...


class FarmingPort(Protocol):
    def allowed(self, account: str, tenant: str, workspace: str) -> bool: ...


class NullAccountCenterPort:
    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference)


class NullBrowserRuntimePort:
    """Bounded test double; it never accesses live TikTok."""

    def publish(
        self, account: str, payload: dict[str, Any], tenant: str, workspace: str
    ) -> bool:
        return bool(account and payload and tenant and workspace)


class NullProxyCenterPort:
    def healthy_for(self, account: str, tenant: str, workspace: str) -> bool:
        return bool(account and tenant and workspace)


class NullFarmingPort:
    def allowed(self, account: str, tenant: str, workspace: str) -> bool:
        return bool(account and tenant and workspace)


class ExistingAccountCenterAdapter:
    def __init__(self, center: Any) -> None:
        self.center = center

    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        account = getattr(self.center, "accounts", {}).get(reference)
        return bool(
            account and account.tenant == tenant and account.workspace == workspace
        )


class ExistingBrowserRuntimeAdapter:
    """Delegates publishing to the existing runtime when it exposes the operation."""

    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime

    def publish(
        self, account: str, payload: dict[str, Any], tenant: str, workspace: str
    ) -> bool:
        publisher = getattr(self.runtime, "publish_content", None)
        if publisher is None:
            return True
        return bool(publisher(account, payload, tenant=tenant, workspace=workspace))


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


class ExistingFarmingAdapter:
    def __init__(self, farming: Any) -> None:
        self.farming = farming

    def allowed(self, account: str, tenant: str, workspace: str) -> bool:
        return (
            not self.farming.kill_switch
            and (
                tenant,
                workspace,
            )
            not in self.farming.paused_workspaces
        )
