"""Narrow ports that reuse existing TikTok centers without owning them."""

from __future__ import annotations

from typing import Protocol

from .models import ClusterBrowserInstance


class BrowserRuntimePort(Protocol):
    def launch_reference(self, instance: ClusterBrowserInstance) -> None: ...
    def stop_reference(self, runtime_reference: str) -> None: ...
    def restore_reference(self, runtime_reference: str) -> bool: ...


class RiskControlPort(Protocol):
    def has_unresolved_restriction(
        self, tenant: str, workspace: str, account_reference: str
    ) -> bool: ...


class ReferenceBrowserRuntime:
    def launch_reference(self, instance: ClusterBrowserInstance) -> None:
        del instance

    def stop_reference(self, runtime_reference: str) -> None:
        del runtime_reference

    def restore_reference(self, runtime_reference: str) -> bool:
        return bool(runtime_reference)


class PermissiveRiskControl:
    def has_unresolved_restriction(
        self, tenant: str, workspace: str, account_reference: str
    ) -> bool:
        del tenant, workspace, account_reference
        return False
