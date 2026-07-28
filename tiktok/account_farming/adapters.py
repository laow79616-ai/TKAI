"""Bounded integration ports for existing TikTok platform services."""

from __future__ import annotations

from typing import Any, Protocol


class AccountCenterPort(Protocol):
    def validate(self, reference: str, tenant: str, workspace: str) -> bool: ...
    def pause(
        self, reference: str, tenant: str, workspace: str, reason: str
    ) -> None: ...


class BrowserRuntimePort(Protocol):
    def acquire(self, reference: str, tenant: str, workspace: str) -> str: ...
    def healthy(self, reference: str, tenant: str, workspace: str) -> bool: ...
    def restore(self, reference: str, tenant: str, workspace: str) -> bool: ...
    def release(self, reference: str, tenant: str, workspace: str) -> None: ...


class ProxyCenterPort(Protocol):
    def acquire(self, reference: str, tenant: str, workspace: str) -> str: ...
    def healthy(self, reference: str, tenant: str, workspace: str) -> bool: ...
    def replace(self, reference: str, tenant: str, workspace: str) -> str: ...
    def release(self, reference: str, tenant: str, workspace: str) -> None: ...


class BoundedAccountCenterAdapter:
    def __init__(self, center: Any) -> None:
        self.center = center

    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        account = getattr(self.center, "accounts", {}).get(reference)
        return bool(
            account and account.tenant == tenant and account.workspace == workspace
        )

    def pause(self, reference: str, tenant: str, workspace: str, reason: str) -> None:
        account = getattr(self.center, "accounts", {}).get(reference)
        if account and account.tenant == tenant and account.workspace == workspace:
            account.auto_paused = True


class NullBrowserRuntimePort:
    """Safe test double: allocates references but performs no browsing."""

    def acquire(self, reference: str, tenant: str, workspace: str) -> str:
        return f"browser://{tenant}/{workspace}/{reference}"

    def healthy(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference)

    def restore(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference)

    def release(self, reference: str, tenant: str, workspace: str) -> None:
        return None


class NullProxyCenterPort:
    """Safe test double: never connects to a live proxy."""

    def acquire(self, reference: str, tenant: str, workspace: str) -> str:
        return f"proxy://{tenant}/{workspace}/{reference}"

    def healthy(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference)

    def replace(self, reference: str, tenant: str, workspace: str) -> str:
        return f"{reference}/replacement"

    def release(self, reference: str, tenant: str, workspace: str) -> None:
        return None


class NullAccountCenterPort:
    def validate(self, reference: str, tenant: str, workspace: str) -> bool:
        return bool(reference)

    def pause(self, reference: str, tenant: str, workspace: str, reason: str) -> None:
        return None


class ExistingBrowserRuntimeAdapter:
    """Scoped adapter to the existing Browser Runtime pool."""

    def __init__(self, runtime: Any) -> None:
        self.runtime = runtime

    @staticmethod
    def _scope(tenant: str, workspace: str):
        from tiktok.browser_runtime import RuntimeScope

        return RuntimeScope(
            tenant,
            workspace,
            "account-farming",
            frozenset({"tiktok:browser:control", "tiktok:browser:read"}),
        )

    def acquire(self, reference: str, tenant: str, workspace: str) -> str:
        instance = self.runtime.acquire(
            self._scope(tenant, workspace), account_reference=reference
        )
        return instance.id

    def healthy(self, reference: str, tenant: str, workspace: str) -> bool:
        instance = self.runtime.instances.get(reference)
        return bool(
            instance
            and instance.tenant == tenant
            and instance.workspace == workspace
            and instance.status.value in {"running", "idle"}
        )

    def restore(self, reference: str, tenant: str, workspace: str) -> bool:
        # Browser Runtime owns encrypted storage restoration during acquisition.
        return self.healthy(reference, tenant, workspace)

    def release(self, reference: str, tenant: str, workspace: str) -> None:
        self.runtime.release(reference, self._scope(tenant, workspace))


class ExistingProxyCenterAdapter:
    """Scoped adapter to the existing Proxy Center pool."""

    def __init__(self, center: Any) -> None:
        self.center = center

    @staticmethod
    def _scope(tenant: str, workspace: str):
        from tiktok.proxy_center import ProxyScope

        return ProxyScope(
            tenant,
            workspace,
            "account-farming",
            frozenset(
                {
                    "tiktok:proxy:acquire",
                    "tiktok:proxy:release",
                    "tiktok:proxy:rotate",
                }
            ),
        )

    def acquire(self, reference: str, tenant: str, workspace: str) -> str:
        from tiktok.proxy_center import BindingTarget

        allocation = self.center.acquire(
            self._scope(tenant, workspace),
            target_type=BindingTarget.TIKTOK_ACCOUNT,
            target_reference=reference,
        )
        return allocation.id

    def healthy(self, reference: str, tenant: str, workspace: str) -> bool:
        allocation = self.center.allocations.get(reference)
        if not allocation:
            return False
        record = self.center.health.get(allocation.proxy_id)
        return bool(
            allocation.tenant == tenant
            and allocation.workspace == workspace
            and (record is None or record.health_score >= 50)
        )

    def replace(self, reference: str, tenant: str, workspace: str) -> str:
        return self.center.rotate(
            reference, self._scope(tenant, workspace), reason="bounded-recovery"
        ).id

    def release(self, reference: str, tenant: str, workspace: str) -> None:
        self.center.release(reference, self._scope(tenant, workspace))
