"""Bounded adapter from browser runtime events to TikTok Account Center."""

from __future__ import annotations

from tiktok.account_center import AccountScope, AccountStatus, TikTokAccountCenter


class AccountCenterStatusAdapter:
    def __init__(self, center: TikTokAccountCenter) -> None:
        self.center = center

    @staticmethod
    def _scope(tenant: str, workspace: str) -> AccountScope:
        return AccountScope(
            tenant,
            workspace,
            "browser-runtime",
            frozenset({"tiktok:write", "tiktok:risk"}),
        )

    def update_login_status(
        self,
        account_reference: str,
        tenant: str,
        workspace: str,
        *,
        logged_in: bool,
        expired: bool,
        risk: str,
    ) -> None:
        if not account_reference or account_reference not in self.center.accounts:
            return
        status = (
            AccountStatus.EXPIRED_SESSION
            if expired
            else AccountStatus.LOGGED_IN
            if logged_in
            else AccountStatus.LOGGED_OUT
        )
        self.center.set_status(
            account_reference, status, self._scope(tenant, workspace)
        )

    def auto_pause(
        self, account_reference: str, tenant: str, workspace: str, reason: str
    ) -> None:
        if not account_reference or account_reference not in self.center.accounts:
            return
        account = self.center.accounts[account_reference]
        scope = self._scope(tenant, workspace)
        self.center._scoped(account, scope)
        account.auto_paused = True
        account.status = AccountStatus.OFFLINE
        self.center._audit("browser_runtime.auto_pause", account_reference, scope)
