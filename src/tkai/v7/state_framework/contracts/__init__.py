"""Immutable contracts for the V7 Unified State Management Framework."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from hashlib import sha256
from typing import Any, Protocol, cast, runtime_checkable

from tkai.v7.security import filter_secrets


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Lifecycle(str, Enum):
    CREATED = "created"
    INITIALIZED = "initialized"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    RECOVERING = "recovering"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ARCHIVED = "archived"
    DELETED = "deleted"


class HealthStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class StateScope:
    tenant_reference: str
    workspace_reference: str


@dataclass(frozen=True)
class StateHealth:
    status: HealthStatus = HealthStatus.UNKNOWN
    checked_at: str = field(default_factory=utc_now)
    details: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True)
class StateRecord:
    state_id: str
    state_type: str
    owner: str
    version: int
    lifecycle: Lifecycle
    current_state: str
    previous_state: str | None
    scope: StateScope
    transition_history: tuple[str, ...] = ()
    snapshot_reference: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)
    health: StateHealth = field(default_factory=StateHealth)
    metrics: Mapping[str, float] = field(default_factory=dict)
    audit: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.state_id or not self.state_type or not self.owner:
            raise ValueError("state id, type, and owner are required")
        if self.version < 1:
            raise ValueError("state version must be positive")
        object.__setattr__(self, "metadata", filter_secrets(self.metadata))


StateModel = StateRecord
StateLifecycle = Lifecycle


@dataclass(frozen=True)
class Transition:
    transition_id: str
    state_id: str
    from_state: str
    to_state: str
    from_lifecycle: Lifecycle
    to_lifecycle: Lifecycle
    from_version: int
    to_version: int
    actor: str
    reason: str = ""
    compatibility: bool = False
    timestamp: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class Snapshot:
    snapshot_id: str
    state_id: str
    state_version: int
    state_reference: str
    lifecycle: Lifecycle
    current_state: str
    previous_state: str | None
    metadata: Mapping[str, object]
    integrity_hash: str
    created_by: str
    created_at: str = field(default_factory=utc_now)

    @classmethod
    def create(
        cls, state: StateRecord, state_reference: str, created_by: str
    ) -> Snapshot:
        if not state_reference or "://" not in state_reference:
            raise ValueError("snapshot payload must be a reference")
        metadata = filter_secrets(state.metadata)
        content = {
            "state_id": state.state_id,
            "state_version": state.version,
            "state_reference": state_reference,
            "lifecycle": state.lifecycle.value,
            "current_state": state.current_state,
            "previous_state": state.previous_state,
            "metadata": metadata,
        }
        digest = sha256(
            json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return cls(
            snapshot_id=f"{state.state_id}:v{state.version}:{digest[:12]}",
            state_id=state.state_id,
            state_version=state.version,
            state_reference=state_reference,
            lifecycle=state.lifecycle,
            current_state=state.current_state,
            previous_state=state.previous_state,
            metadata=metadata,
            integrity_hash=digest,
            created_by=created_by,
        )

    def verify(self) -> bool:
        content = {
            "state_id": self.state_id,
            "state_version": self.state_version,
            "state_reference": self.state_reference,
            "lifecycle": self.lifecycle.value,
            "current_state": self.current_state,
            "previous_state": self.previous_state,
            "metadata": self.metadata,
        }
        digest = sha256(
            json.dumps(content, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        return digest == self.integrity_hash


@dataclass(frozen=True)
class HistoryEntry:
    entry_id: str
    state_id: str
    category: str
    action: str
    actor: str
    reference: str | None = None
    details: Mapping[str, object] = field(default_factory=dict)
    timestamp: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    state_id: str
    severity: str = "error"


@dataclass(frozen=True)
class ValidationReport:
    state_id: str
    valid: bool
    issues: tuple[ValidationIssue, ...] = ()
    checked_at: str = field(default_factory=utc_now)


@dataclass(frozen=True)
class RecoveryPlan:
    recovery_id: str
    state_id: str
    snapshot_reference: str
    target_version: int
    ready: bool
    valid: bool
    simulated: bool = True
    issues: tuple[str, ...] = ()
    created_at: str = field(default_factory=utc_now)


@runtime_checkable
class StatePersistence(Protocol):
    def save(self, state: StateRecord) -> None: ...

    def load(self, state_id: str) -> StateRecord | None: ...


def serialize(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "__dataclass_fields__"):
        return {key: serialize(item) for key, item in asdict(cast(Any, value)).items()}
    if isinstance(value, Mapping):
        return {str(key): serialize(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [serialize(item) for item in value]
    return value


__all__ = (
    "HealthStatus",
    "HistoryEntry",
    "Lifecycle",
    "RecoveryPlan",
    "Snapshot",
    "StateHealth",
    "StateLifecycle",
    "StateModel",
    "StatePersistence",
    "StateRecord",
    "StateScope",
    "Transition",
    "ValidationIssue",
    "ValidationReport",
    "serialize",
    "utc_now",
)
