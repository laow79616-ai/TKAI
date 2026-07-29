"""Bounded domain contracts for the enterprise TikTok Resource Center."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, IntEnum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ResourceType(str, Enum):
    ACCOUNT = "account"
    BROWSER = "browser"
    BROWSER_CLUSTER_NODE = "browser_cluster_node"
    DEVICE = "device"
    PROXY = "proxy"
    WORKFLOW = "workflow"
    WORKER = "worker"
    QUEUE = "queue"
    RUNTIME = "runtime"
    STORAGE = "storage"
    CUSTOM_REFERENCE = "custom_resource_reference"


class ResourceStatus(str, Enum):
    DISCOVERED = "discovered"
    REGISTERED = "registered"
    RESERVED = "reserved"
    ALLOCATED = "allocated"
    RUNNING = "running"
    IDLE = "idle"
    PAUSED = "paused"
    RECOVERING = "recovering"
    RELEASED = "released"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Priority(IntEnum):
    LOW = 25
    NORMAL = 50
    HIGH = 75
    CRITICAL = 100


class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


SECRET_KEYS = frozenset(
    {
        "password",
        "secret",
        "token",
        "cookie",
        "cookies",
        "credential",
        "credentials",
        "session",
        "api_key",
        "proxy_password",
    }
)


def validate_safe_mapping(value: dict[str, Any], maximum_bytes: int = 16_384) -> None:
    """Reject secrets, executable fields, unsafe values, and unbounded metadata."""

    forbidden = {"code", "command", "script", "shell", "executable"}

    def walk(item: Any) -> None:
        if isinstance(item, dict):
            keys = {str(key).casefold() for key in item}
            if keys & SECRET_KEYS:
                raise ValueError("Secrets and credentials are forbidden.")
            if keys & forbidden:
                raise ValueError("Executable resource metadata is forbidden.")
            for child in item.values():
                walk(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)
        elif not isinstance(item, (str, int, float, bool, type(None))):
            raise TypeError("Resource metadata must contain JSON-safe values.")

    walk(value)
    if len(json.dumps(value).encode()) > maximum_bytes:
        raise ValueError("Resource metadata exceeds the bounded size.")


@dataclass(frozen=True, slots=True)
class ResourceScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:resources:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class Resource:
    id: str
    name: str
    resource_type: ResourceType
    tenant: str
    workspace: str
    owner: str
    status: ResourceStatus = ResourceStatus.DISCOVERED
    version: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: frozenset[str] = frozenset()
    group: str = ""
    encrypted_reference: str = ""
    maximum_capacity: float = 1.0
    current_usage: float = 0.0
    health: HealthState = HealthState.UNKNOWN
    restriction_active: bool = False
    challenge_active: bool = False
    discovered_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.owner)):
            raise ValueError("Resource identity, scope, and owner are required.")
        if self.version < 1:
            raise ValueError("Resource version must be positive.")
        if self.maximum_capacity <= 0 or self.current_usage < 0:
            raise ValueError("Resource capacity and usage must be bounded.")
        if self.current_usage > self.maximum_capacity:
            raise ValueError("Resource usage cannot exceed maximum capacity.")
        if self.encrypted_reference and not self.encrypted_reference.startswith(
            ("vault://", "encrypted://", "reference://")
        ):
            raise ValueError("External references must be encrypted or opaque.")
        validate_safe_mapping(self.metadata)
        if any(not tag or len(tag) > 64 for tag in self.tags):
            raise ValueError("Tags must be non-empty and at most 64 characters.")


@dataclass(slots=True)
class Reservation:
    id: str
    resource_id: str
    tenant: str
    workspace: str
    owner: str
    start_time: datetime
    expires_at: datetime
    priority: Priority = Priority.NORMAL
    heartbeat_at: datetime = field(default_factory=utcnow)
    cancelled: bool = False


@dataclass(slots=True)
class Allocation:
    id: str
    resource_id: str
    tenant: str
    workspace: str
    owner: str
    priority: Priority
    allocated_at: datetime
    reservation_id: str = ""
    released_at: datetime | None = None
    cooldown_until: datetime | None = None


@dataclass(slots=True)
class Lease:
    id: str
    allocation_id: str
    resource_id: str
    tenant: str
    workspace: str
    owner: str
    started_at: datetime
    expires_at: datetime
    renewed_at: datetime
    active: bool = True


@dataclass(slots=True)
class Quota:
    workspace: int = 1000
    account: int = 100
    browser: int = 100
    device: int = 100
    proxy: int = 100
    worker: int = 100
    task: int = 1000

    def validate(self) -> None:
        values = (
            self.workspace,
            self.account,
            self.browser,
            self.device,
            self.proxy,
            self.worker,
            self.task,
        )
        if any(value < 0 or value > 1_000_000 for value in values):
            raise ValueError("Quotas must be within [0, 1000000].")


@dataclass(slots=True)
class UtilizationSample:
    tenant: str
    workspace: str
    captured_at: datetime = field(default_factory=utcnow)
    cpu: float = 0.0
    memory: float = 0.0
    browser_slots: float = 0.0
    devices: float = 0.0
    workers: float = 0.0
    queue_usage: float = 0.0
    proxy_usage: float = 0.0
    account_usage: float = 0.0

    def validate(self) -> None:
        values = (
            self.cpu,
            self.memory,
            self.browser_slots,
            self.devices,
            self.workers,
            self.queue_usage,
            self.proxy_usage,
            self.account_usage,
        )
        if any(value < 0 or value > 1 for value in values):
            raise ValueError("Utilization ratios must be within [0, 1].")

    @property
    def ratio(self) -> float:
        return (
            sum(
                (
                    self.cpu,
                    self.memory,
                    self.browser_slots,
                    self.devices,
                    self.workers,
                    self.queue_usage,
                    self.proxy_usage,
                    self.account_usage,
                )
            )
            / 8
        )
