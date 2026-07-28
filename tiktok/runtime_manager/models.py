"""Domain contracts for the local enterprise TikTok Runtime Manager."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class RuntimeStatus(str, Enum):
    INITIALIZING = "initializing"
    STARTING = "starting"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    RECOVERING = "recovering"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ARCHIVED = "archived"
    DELETED = "deleted"


class ServiceStatus(str, Enum):
    REGISTERED = "registered"
    STARTING = "starting"
    RUNNING = "running"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"
    RECOVERING = "recovering"


class HealthState(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    BLOCKED = "blocked"


class RestartMode(str, Enum):
    NEVER = "never"
    ON_FAILURE = "on_failure"
    ALWAYS = "always"
    MANUAL_APPROVAL = "manual_approval"


@dataclass(frozen=True, slots=True)
class RuntimeScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:runtime:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


SECRET_KEYS = frozenset(
    {"password", "secret", "token", "cookie", "credentials", "session", "api_key"}
)


def validate_safe_mapping(value: dict[str, Any], maximum_bytes: int = 65536) -> None:
    def walk(item: Any) -> None:
        if isinstance(item, dict):
            for key, child in item.items():
                if str(key).casefold() in SECRET_KEYS:
                    raise ValueError(
                        "Secret material is forbidden in runtime metadata."
                    )
                walk(child)
        elif isinstance(item, (list, tuple)):
            for child in item:
                walk(child)
        elif not isinstance(item, (str, int, float, bool, type(None))):
            raise TypeError("Runtime metadata must be JSON-safe.")

    walk(value)
    if len(json.dumps(value).encode()) > maximum_bytes:
        raise ValueError("Runtime metadata exceeds the bounded size.")


@dataclass(slots=True)
class RuntimeInstance:
    id: str
    name: str
    workspace: str
    owner: str
    version: str
    tenant: str = "default"
    status: RuntimeStatus = RuntimeStatus.INITIALIZING
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utcnow)
    updated_at: datetime = field(default_factory=utcnow)

    def validate(self) -> None:
        if not all(
            (self.id, self.name, self.workspace, self.owner, self.version, self.tenant)
        ):
            raise ValueError(
                "Runtime identity, scope, owner, and version are required."
            )
        validate_safe_mapping(self.metadata)


@dataclass(slots=True)
class RestartPolicy:
    mode: RestartMode = RestartMode.ON_FAILURE
    maximum_attempts: int = 3
    backoff_seconds: int = 5
    cooldown_seconds: int = 30
    approval_required: bool = False

    def validate(self, maximum_attempts: int) -> None:
        if not 0 <= self.maximum_attempts <= maximum_attempts:
            raise ValueError("Restart attempts exceed the bounded runtime limit.")
        if not 0 <= self.backoff_seconds <= 3600:
            raise ValueError("Backoff must be within [0, 3600] seconds.")
        if not 0 <= self.cooldown_seconds <= 86400:
            raise ValueError("Cooldown must be within [0, 86400] seconds.")


@dataclass(slots=True)
class ManagedService:
    id: str
    name: str
    tenant: str
    workspace: str
    version: str
    capabilities: frozenset[str] = frozenset()
    dependencies: frozenset[str] = frozenset()
    status: ServiceStatus = ServiceStatus.REGISTERED
    health: HealthState = HealthState.UNKNOWN
    heartbeat_at: datetime = field(default_factory=utcnow)
    restart_policy: RestartPolicy = field(default_factory=RestartPolicy)
    restart_count: int = 0
    recovery_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def validate(self, maximum_attempts: int) -> None:
        if not all((self.id, self.name, self.tenant, self.workspace, self.version)):
            raise ValueError("Service identity, scope, and version are required.")
        if self.id in self.dependencies:
            raise ValueError("A service cannot depend on itself.")
        self.restart_policy.validate(maximum_attempts)
        validate_safe_mapping(self.metadata)


@dataclass(slots=True)
class RuntimeProcess:
    id: str
    service_id: str
    tenant: str
    workspace: str
    pid_reference: str
    status: str = "running"
    started_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class RuntimeWorker:
    id: str
    service_id: str
    tenant: str
    workspace: str
    status: str = "idle"
    queue_depth: int = 0
    heartbeat_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class RuntimeEvent:
    kind: str
    runtime_id: str
    service_id: str
    tenant: str
    workspace: str
    actor: str
    detail: str = ""
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class RuntimeLimits:
    maximum_services: int = 64
    maximum_processes: int = 256
    maximum_workers: int = 512
    maximum_restart_attempts: int = 8
    maximum_recovery_attempts: int = 5
    startup_timeout_seconds: int = 300
    shutdown_timeout_seconds: int = 300
    heartbeat_timeout_seconds: int = 60
    coordination_timeout_seconds: int = 300

    def validate(self) -> None:
        values = (
            self.__dict__
            if hasattr(self, "__dict__")
            else {field: getattr(self, field) for field in self.__dataclass_fields__}
        )
        if any(not isinstance(value, int) or value <= 0 for value in values.values()):
            raise ValueError("Runtime limits must be positive bounded integers.")
        if self.maximum_services > 1024 or self.maximum_recovery_attempts > 100:
            raise ValueError("Runtime limits exceed safe local bounds.")
