"""Typed TikTok Account Center domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from enum import Enum
from typing import Any


class AccountStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    LOGGED_IN = "logged_in"
    LOGGED_OUT = "logged_out"
    EXPIRED_COOKIE = "expired_cookie"
    EXPIRED_SESSION = "expired_session"
    RESTRICTED = "restricted"
    SUSPENDED = "suspended"
    BANNED = "banned"
    ARCHIVED = "archived"
    DELETED = "deleted"


class LoginMethod(str, Enum):
    COOKIE = "cookie"
    SESSION = "session"
    QR = "qr"
    RESTORE = "restore"


@dataclass(frozen=True, slots=True)
class AccountScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class TikTokProfile:
    nickname: str = ""
    avatar: str = ""
    bio: str = ""
    website: str = ""
    category: str = ""
    language: str = "en"
    region: str = ""
    birthday: date | None = None
    username: str = ""


@dataclass(slots=True)
class BrowserBinding:
    profile_reference: str
    engine: str = "chromium"
    automation: str = "playwright"
    fingerprint_reference: str = ""
    user_agent: str = ""
    timezone: str = "UTC"
    language: str = "en"
    resolution: str = "1920x1080"
    proxy_reference: str = ""


@dataclass(slots=True)
class TikTokAccount:
    id: str
    tenant: str
    workspace: str
    profile: TikTokProfile
    status: AccountStatus = AccountStatus.LOGGED_OUT
    group_ids: set[str] = field(default_factory=set)
    tag_ids: set[str] = field(default_factory=set)
    project: str = ""
    business_unit: str = ""
    browser: BrowserBinding | None = None
    risk_score: float = 0
    auto_paused: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["status"] = self.status.value
        value["group_ids"] = sorted(self.group_ids)
        value["tag_ids"] = sorted(self.tag_ids)
        return value


@dataclass(slots=True)
class AccountGroup:
    id: str
    name: str
    tenant: str
    workspace: str
    parent_id: str = ""
    project: str = ""
    business_unit: str = ""


@dataclass(slots=True)
class AccountTag:
    id: str
    name: str
    tenant: str
    workspace: str
    color: str = ""


@dataclass(frozen=True, slots=True)
class RiskEvent:
    account_id: str
    kind: str
    score: float
    detail: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass(frozen=True, slots=True)
class AuditEntry:
    action: str
    actor: str
    tenant: str
    workspace: str
    resource_id: str
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
