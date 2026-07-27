"""Bounded Proxy Center integration contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .models import BindingTarget, ProxyEndpoint, ProxyScope

if TYPE_CHECKING:
    from .service import TikTokProxyCenter


class ProxyAllocationPort(Protocol):
    def acquire_for_launch(
        self,
        scope: ProxyScope,
        *,
        browser_reference: str,
        account_reference: str = "",
        region: str = "",
        country: str = "",
    ) -> ProxyEndpoint: ...

    def release_from_launch(
        self, proxy_id: str, browser_reference: str, scope: ProxyScope
    ) -> None: ...


class BrowserRuntimeProxyAdapter:
    """Narrow secret-free interface presented to TikTok Browser Runtime."""

    def __init__(self, center: TikTokProxyCenter) -> None:
        self.center = center

    def acquire_for_launch(
        self,
        scope: ProxyScope,
        *,
        browser_reference: str,
        account_reference: str = "",
        region: str = "",
        country: str = "",
    ) -> ProxyEndpoint:
        target_type = (
            BindingTarget.TIKTOK_ACCOUNT
            if account_reference
            else BindingTarget.BROWSER_RUNTIME
        )
        target = account_reference or browser_reference
        allocation = self.center.acquire(
            scope,
            target_type=target_type,
            target_reference=target,
            region=region,
            country=country,
        )
        proxy = self.center.get(allocation.proxy_id, scope)
        return ProxyEndpoint(
            proxy.id,
            proxy.protocol.value,
            proxy.host,
            proxy.port,
            proxy.credential_reference,
        )

    def release_from_launch(
        self, proxy_id: str, browser_reference: str, scope: ProxyScope
    ) -> None:
        allocation = next(
            (
                item
                for item in self.center.allocations.values()
                if item.proxy_id == proxy_id
                and item.target_reference == browser_reference
                and item.released_at is None
            ),
            None,
        )
        if allocation:
            self.center.release(allocation.id, scope)
