"""Domain models for the bounded local TikTok browser cluster."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ClusterStatus(str, Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    SCALING = "scaling"
    PAUSED = "paused"
    RECOVERING = "recovering"
    MAINTENANCE = "maintenance"
    ARCHIVED = "archived"
    DELETED = "deleted"


class NodeStatus(str, Enum):
    READY = "ready"
    DRAINING = "draining"
    OFFLINE = "offline"
    RECOVERING = "recovering"


class InstanceStatus(str, Enum):
    QUEUED = "queued"
    LAUNCHING = "launching"
    RUNNING = "running"
    IDLE = "idle"
    PAUSED = "paused"
    RECOVERING = "recovering"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass(frozen=True, slots=True)
class ClusterScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:browser-cluster:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class BrowserCluster:
    id: str
    name: str
    description: str
    tenant: str
    workspace: str
    owner: str
    version: str = "5.0"
    status: ClusterStatus = ClusterStatus.INITIALIZING
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ClusterNode:
    id: str
    cluster_id: str
    tenant: str
    workspace: str
    hostname: str
    capacity: int
    cpu_capacity: float
    memory_capacity_mb: int
    browser_slots: int
    status: NodeStatus = NodeStatus.READY
    running_browsers: int = 0
    idle_browsers: int = 0
    health: str = "healthy"
    heartbeat: datetime = field(default_factory=utcnow)
    cpu_usage: float = 0.0
    memory_usage_mb: int = 0


@dataclass(slots=True)
class ClusterBrowserInstance:
    id: str
    cluster_id: str
    tenant: str
    workspace: str
    browser_runtime_reference: str
    browser_profile: str
    account_reference: str
    proxy_reference: str = ""
    node_id: str = ""
    status: InstanceStatus = InstanceStatus.QUEUED
    creation_time: datetime = field(default_factory=utcnow)
    last_active: datetime = field(default_factory=utcnow)
    health: str = "unknown"
    cpu_reservation: float = 0.0
    memory_reservation_mb: int = 0


@dataclass(slots=True)
class BrowserProfileTemplate:
    id: str
    tenant: str
    workspace: str
    name: str
    version: int
    kind: str = "default"
    account_reference: str = ""
    settings: dict[str, Any] = field(default_factory=dict)

    def validate(self) -> None:
        if not self.id or not self.name or self.version < 1:
            raise ValueError("Profile ID, name, and positive version are required.")
        if self.kind not in {"default", "workspace", "account", "shared"}:
            raise ValueError("Unsupported browser profile kind.")
        if self.kind == "account" and not self.account_reference:
            raise ValueError("Account profiles require an account reference.")
        forbidden = {"secret", "password", "token", "cookie"}
        if any(any(word in key.lower() for word in forbidden) for key in self.settings):
            raise ValueError("Profile settings must contain references, not secrets.")


@dataclass(order=True, slots=True)
class QueueItem:
    sort_key: tuple[int, datetime, int]
    id: str = field(compare=False)
    instance_id: str = field(compare=False)
    tenant: str = field(compare=False)
    workspace: str = field(compare=False)
    account_reference: str = field(compare=False)
    priority: int = field(compare=False, default=0)
    attempts: int = field(compare=False, default=0)


@dataclass(slots=True)
class ResourcePolicy:
    cpu_budget: float = 8.0
    memory_budget_mb: int = 16384
    maximum_browser_count: int = 20
    maximum_parallel_launches: int = 4
    workspace_limit: int = 10
    account_limit: int = 1

    def validate(self) -> None:
        if self.cpu_budget <= 0 or min(
            self.memory_budget_mb,
            self.maximum_browser_count,
            self.maximum_parallel_launches,
            self.workspace_limit,
            self.account_limit,
        ) < 1:
            raise ValueError("Cluster resource limits must be positive.")
        if self.maximum_parallel_launches > self.maximum_browser_count:
            raise ValueError("Parallel launches cannot exceed browser count.")


@dataclass(slots=True)
class RecoveryPolicy:
    maximum_attempts: int = 3
    backoff_seconds: float = 2.0
    cooldown_seconds: float = 30.0
    manual_approval: bool = False

    def validate(self) -> None:
        if self.maximum_attempts < 1 or min(
            self.backoff_seconds, self.cooldown_seconds
        ) < 0:
            raise ValueError("Recovery policy values are invalid.")


@dataclass(slots=True)
class RecoveryRecord:
    instance_id: str
    attempts: int
    reason: str
    action: str
    recovered: bool
    stopped_for_restriction: bool = False
    occurred_at: datetime = field(default_factory=utcnow)


def serialize(value: Any) -> dict[str, Any]:
    result = asdict(value)
    for key, item in tuple(result.items()):
        if isinstance(item, Enum):
            result[key] = item.value
        elif isinstance(item, datetime):
            result[key] = item.isoformat()
    return result
