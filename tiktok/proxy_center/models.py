"""Typed domain models for the enterprise TikTok Proxy Center."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ProxyType(str, Enum):
    IPV4 = "ipv4"
    IPV6 = "ipv6"
    MIXED_POOL = "mixed_pool"


class ProxyProtocol(str, Enum):
    HTTP = "http"
    HTTPS = "https"
    SOCKS5 = "socks5"


class ProxyStatus(str, Enum):
    DRAFT = "draft"
    AVAILABLE = "available"
    IN_USE = "in_use"
    COOLING = "cooling"
    DISABLED = "disabled"
    EXPIRED = "expired"
    ARCHIVED = "archived"
    DELETED = "deleted"


class GroupType(str, Enum):
    STATIC_POOL = "static_pool"
    DYNAMIC_POOL = "dynamic_pool"
    RESIDENTIAL = "residential"
    DATACENTER = "datacenter"
    MOBILE = "mobile"
    COUNTRY_GROUP = "country_group"
    PROJECT_GROUP = "project_group"
    ACCOUNT_GROUP = "account_group"


class RotationMode(str, Enum):
    MANUAL = "manual"
    INTERVAL = "interval"
    REQUEST_COUNT = "request_count"
    SESSION_BASED = "session_based"
    ACCOUNT_BASED = "account_based"
    WORKSPACE_BASED = "workspace_based"
    FAILURE_TRIGGER = "failure_trigger"


class BindingTarget(str, Enum):
    BROWSER_RUNTIME = "browser_runtime"
    TIKTOK_ACCOUNT = "tiktok_account"
    WORKSPACE = "workspace"
    PROJECT = "project"
    AUTOMATION_WORKFLOW = "automation_workflow"


@dataclass(frozen=True, slots=True)
class ProxyScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:proxy:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Proxy:
    id: str
    name: str
    tenant: str
    workspace: str
    type: ProxyType
    protocol: ProxyProtocol
    host: str
    port: int
    credential_reference: str = ""
    provider: str = ""
    region: str = ""
    country: str = ""
    isp: str = ""
    status: ProxyStatus = ProxyStatus.DRAFT
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not self.id or not self.name or not self.host:
            raise ValueError("Proxy ID, name, and host are required.")
        if not 1 <= self.port <= 65535:
            raise ValueError("Proxy port must be within [1, 65535].")
        forbidden = {"username", "password", "secret", "token"}
        if forbidden & {key.casefold() for key in self.metadata}:
            raise ValueError("Proxy metadata cannot contain secrets.")
        if "://" in self.host or "@" in self.host:
            raise ValueError("Proxy host must not embed protocol or credentials.")

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        for key in ("type", "protocol", "status"):
            result[key] = getattr(self, key).value
        result["created_at"] = self.created_at.isoformat()
        result["updated_at"] = self.updated_at.isoformat()
        return result


@dataclass(slots=True)
class ProxyGroup:
    id: str
    name: str
    tenant: str
    workspace: str
    type: GroupType
    proxy_ids: set[str] = field(default_factory=set)
    dynamic_filter: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class HealthRecord:
    proxy_id: str
    connectivity: bool
    latency_seconds: float
    bandwidth_reference: str = ""
    availability: float = 0
    success_rate: float = 0
    failure_rate: float = 0
    consecutive_failures: int = 0
    health_score: float = 0
    last_check: datetime = field(default_factory=utcnow)
    checks: dict[str, bool] = field(default_factory=dict)


@dataclass(slots=True)
class VerificationResult:
    proxy_id: str
    dns_resolution: bool
    tcp_connectivity: bool
    tls_handshake: bool
    public_ip_check: bool
    geo_check: bool
    protocol_validation: bool
    authentication_validation: bool
    latency_seconds: float
    public_ip: str = ""
    checked_at: datetime = field(default_factory=utcnow)

    @property
    def successful(self) -> bool:
        return all(
            (
                self.dns_resolution,
                self.tcp_connectivity,
                self.protocol_validation,
                self.authentication_validation,
            )
        )


@dataclass(slots=True)
class RotationPolicy:
    id: str
    tenant: str
    workspace: str
    mode: RotationMode
    group_reference: str = ""
    interval_seconds: int = 0
    request_limit: int = 0
    cooldown_seconds: int = 60
    failure_threshold: int = 3


@dataclass(slots=True)
class ProxyBinding:
    id: str
    tenant: str
    workspace: str
    target_type: BindingTarget
    target_reference: str
    proxy_reference: str = ""
    group_reference: str = ""
    priority: int = 0
    affinity: str = ""
    sticky_session_reference: str = ""


@dataclass(order=True, slots=True)
class AllocationRequest:
    sort_key: tuple[int, datetime, int]
    id: str = field(compare=False)
    tenant: str = field(compare=False)
    workspace: str = field(compare=False)
    target_type: BindingTarget = field(compare=False)
    target_reference: str = field(compare=False)
    priority: int = field(compare=False, default=0)
    region_preference: str = field(compare=False, default="")
    country_preference: str = field(compare=False, default="")
    timeout_seconds: float = field(compare=False, default=10)
    retries: int = field(compare=False, default=2)
    cancelled: bool = field(compare=False, default=False)


@dataclass(slots=True)
class Allocation:
    id: str
    proxy_id: str
    tenant: str
    workspace: str
    target_type: BindingTarget
    target_reference: str
    acquired_at: datetime = field(default_factory=utcnow)
    released_at: datetime | None = None
    reserved: bool = False


@dataclass(slots=True)
class UsageEvent:
    proxy_id: str
    tenant: str
    workspace: str
    successful: bool
    latency_seconds: float
    allocation_id: str = ""
    occurred_at: datetime = field(default_factory=utcnow)


@dataclass(frozen=True, slots=True)
class ProxyEndpoint:
    """Secret-free browser launch contract."""

    proxy_id: str
    protocol: str
    host: str
    port: int
    credential_reference: str
