"""Enterprise TikTok Account Center service."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from typing import Any
from uuid import uuid4

from .metrics import TikTokMetrics
from .models import (
    AccountGroup,
    AccountScope,
    AccountStatus,
    AccountTag,
    AuditEntry,
    LoginMethod,
    RiskEvent,
    TikTokAccount,
)
from .security import EncryptedStateStore


class TikTokAccountCenter:
    def __init__(
        self, *, encryption_key: bytes | None = None, risk_threshold: float = 70
    ) -> None:
        if not 0 <= risk_threshold <= 100:
            raise ValueError("Risk threshold must be within [0, 100].")
        self.accounts: dict[str, TikTokAccount] = {}
        self.groups: dict[str, AccountGroup] = {}
        self.tags: dict[str, AccountTag] = {}
        self.risks: list[RiskEvent] = []
        self.audit: list[AuditEntry] = []
        self.metrics = TikTokMetrics()
        self._state = EncryptedStateStore(encryption_key)
        self.risk_threshold = risk_threshold

    @staticmethod
    def _require(scope: AccountScope, action: str) -> None:
        if (
            f"tiktok:{action}" not in scope.permissions
            and "tiktok:admin" not in scope.permissions
        ):
            raise PermissionError(f"RBAC permission required: tiktok:{action}")

    @staticmethod
    def _scoped(item: Any, scope: AccountScope) -> None:
        if item.tenant != scope.tenant or item.workspace != scope.workspace:
            raise PermissionError("Cross-workspace TikTok access denied.")

    def _account(self, account_id: str, scope: AccountScope) -> TikTokAccount:
        account = self.accounts[account_id]
        self._scoped(account, scope)
        return account

    def _audit(self, action: str, resource_id: str, scope: AccountScope) -> None:
        self.audit.append(
            AuditEntry(action, scope.actor, scope.tenant, scope.workspace, resource_id)
        )

    def _active(self) -> None:
        self.metrics.set(
            "tiktok_active_accounts_total",
            sum(
                a.status in {AccountStatus.ONLINE, AccountStatus.LOGGED_IN}
                for a in self.accounts.values()
            ),
        )

    def create(self, account: TikTokAccount, scope: AccountScope) -> TikTokAccount:
        self._require(scope, "write")
        self._scoped(account, scope)
        if not account.id or account.id in self.accounts:
            raise ValueError("Account ID must be non-empty and unique.")
        self.accounts[account.id] = account
        self.metrics.increment("tiktok_accounts_total")
        self._audit("account.create", account.id, scope)
        return account

    def import_accounts(
        self, accounts: Iterable[TikTokAccount], scope: AccountScope
    ) -> list[TikTokAccount]:
        self._require(scope, "batch")
        elevated = replace(scope, permissions=scope.permissions | {"tiktok:write"})
        return [self.create(a, elevated) for a in accounts]

    def export_accounts(self, scope: AccountScope) -> list[dict[str, Any]]:
        return [a.to_dict() for a in self.search(scope)]

    def clone(
        self, account_id: str, scope: AccountScope, new_id: str | None = None
    ) -> TikTokAccount:
        self._require(scope, "write")
        return self.create(
            replace(
                self._account(account_id, scope),
                id=new_id or str(uuid4()),
                status=AccountStatus.LOGGED_OUT,
            ),
            scope,
        )

    def set_status(
        self, account_id: str, status: AccountStatus, scope: AccountScope
    ) -> TikTokAccount:
        self._require(scope, "write")
        account = self._account(account_id, scope)
        account.status = status
        self._active()
        self._audit("account.status", account_id, scope)
        return account

    def archive(self, account_id: str, scope: AccountScope) -> TikTokAccount:
        return self.set_status(account_id, AccountStatus.ARCHIVED, scope)

    def delete(self, account_id: str, scope: AccountScope) -> TikTokAccount:
        account = self.set_status(account_id, AccountStatus.DELETED, scope)
        self._state.delete(f"cookie:{account_id}")
        self._state.delete(f"session:{account_id}")
        return account

    def recover(self, account_id: str, scope: AccountScope) -> TikTokAccount:
        self._require(scope, "write")
        account = self._account(account_id, scope)
        if account.status not in {AccountStatus.DELETED, AccountStatus.ARCHIVED}:
            raise ValueError("Only deleted or archived accounts can be recovered.")
        account.status = AccountStatus.LOGGED_OUT
        self._audit("account.recover", account_id, scope)
        return account

    def batch_status(
        self, ids: Iterable[str], status: AccountStatus, scope: AccountScope
    ) -> list[TikTokAccount]:
        self._require(scope, "batch")
        elevated = replace(scope, permissions=scope.permissions | {"tiktok:write"})
        return [self.set_status(i, status, elevated) for i in ids]

    def login(
        self,
        account_id: str,
        method: LoginMethod,
        state: str,
        scope: AccountScope,
        *,
        valid: bool = True,
    ) -> TikTokAccount:
        self._require(scope, "login")
        account = self._account(account_id, scope)
        if account.auto_paused:
            raise PermissionError("Account is auto-paused by risk policy.")
        if method is not LoginMethod.QR and not state:
            self.metrics.increment("tiktok_login_failure_total")
            raise ValueError("Login state is required.")
        if not valid:
            self.metrics.increment("tiktok_login_failure_total")
            account.status = (
                AccountStatus.EXPIRED_COOKIE
                if method is LoginMethod.COOKIE
                else AccountStatus.EXPIRED_SESSION
            )
            self.metrics.increment(
                "tiktok_cookie_expired_total"
                if method is LoginMethod.COOKIE
                else "tiktok_session_expired_total"
            )
            raise PermissionError("Login state is invalid or expired.")
        if state:
            self._state.put(
                ("cookie:" if method is LoginMethod.COOKIE else "session:")
                + account_id,
                state,
            )
        account.status = AccountStatus.LOGGED_IN
        self.metrics.increment("tiktok_login_success_total")
        self._active()
        self._audit(f"login.{method.value}", account_id, scope)
        return account

    def refresh_session(
        self, account_id: str, state: str, scope: AccountScope
    ) -> TikTokAccount:
        return self.login(account_id, LoginMethod.SESSION, state, scope)

    def add_group(self, item: AccountGroup, scope: AccountScope) -> AccountGroup:
        self._require(scope, "groups")
        self._scoped(item, scope)
        if item.id in self.groups:
            raise ValueError("Group ID must be unique.")
        self.groups[item.id] = item
        self._audit("group.create", item.id, scope)
        return item

    def add_tag(self, item: AccountTag, scope: AccountScope) -> AccountTag:
        self._require(scope, "tags")
        self._scoped(item, scope)
        if item.id in self.tags:
            raise ValueError("Tag ID must be unique.")
        self.tags[item.id] = item
        self._audit("tag.create", item.id, scope)
        return item

    def search(
        self,
        scope: AccountScope,
        *,
        query: str = "",
        status: AccountStatus | None = None,
        group: str = "",
        tag: str = "",
    ) -> list[TikTokAccount]:
        self._require(scope, "read")
        q = query.casefold()
        return [
            a
            for a in self.accounts.values()
            if a.tenant == scope.tenant
            and a.workspace == scope.workspace
            and (
                not q
                or q in a.profile.nickname.casefold()
                or q in a.profile.username.casefold()
            )
            and (status is None or a.status is status)
            and (not group or group in a.group_ids)
            and (not tag or tag in a.tag_ids)
        ]

    def assess_risk(
        self,
        account_id: str,
        scope: AccountScope,
        *,
        cookie_valid: bool = True,
        session_valid: bool = True,
        restricted: bool = False,
        banned: bool = False,
    ) -> RiskEvent:
        self._require(scope, "risk")
        account = self._account(account_id, scope)
        score = min(
            100,
            (not cookie_valid) * 25
            + (not session_valid) * 25
            + restricted * 40
            + banned * 100,
        )
        event = RiskEvent(
            account_id,
            "ban" if banned else "restriction" if restricted else "login_health",
            score,
            "Automated validation result",
        )
        account.risk_score = score
        if banned:
            account.status = AccountStatus.BANNED
        elif restricted:
            account.status = AccountStatus.RESTRICTED
        if score >= self.risk_threshold:
            account.auto_paused = True
        self.risks.append(event)
        self.metrics.increment("tiktok_risk_events_total")
        self._audit("risk.assess", account_id, scope)
        return event

    def dashboard(self, scope: AccountScope) -> dict[str, Any]:
        accounts = self.search(scope)
        ids = {a.id for a in accounts}
        risks = [r for r in self.risks if r.account_id in ids]
        return {
            "accounts": len(accounts),
            "status": {
                s.value: sum(a.status is s for a in accounts) for s in AccountStatus
            },
            "risk": {
                "events": len(risks),
                "paused": sum(a.auto_paused for a in accounts),
            },
            "groups": len({g for a in accounts for g in a.group_ids}),
            "tags": len({t for a in accounts for t in a.tag_ids}),
            "sessions": sum(a.status is AccountStatus.LOGGED_IN for a in accounts),
            "cookies": sum(a.status is AccountStatus.EXPIRED_COOKIE for a in accounts),
            "browser": sum(a.browser is not None for a in accounts),
            "statistics": self.metrics.snapshot(),
        }
