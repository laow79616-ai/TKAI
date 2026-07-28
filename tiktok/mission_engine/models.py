"""Domain models for the Enterprise TikTok Autonomous Mission Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MissionState(str, Enum):
    QUEUED = "queued"
    DISPATCHING = "dispatching"
    RUNNING = "running"
    PAUSED = "paused"
    RECOVERING = "recovering"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ApprovalState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RiskState(str, Enum):
    CLEAR = "clear"
    REVIEW = "review"
    RESTRICTED = "restricted"


@dataclass(frozen=True, slots=True)
class MissionScope:
    tenant: str
    workspace: str
    actor: str
    permissions: frozenset[str] = frozenset({"tiktok:mission-engine:read"})

    def __post_init__(self) -> None:
        if not all((self.tenant, self.workspace, self.actor)):
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class ExecutionWindow:
    starts_at: datetime
    ends_at: datetime

    def validate(self) -> None:
        if self.starts_at.tzinfo is None or self.ends_at.tzinfo is None:
            raise ValueError("Execution windows must be timezone-aware.")
        if self.starts_at >= self.ends_at:
            raise ValueError("Execution window end must follow its start.")

    def contains(self, moment: datetime) -> bool:
        return self.starts_at <= moment <= self.ends_at


@dataclass(slots=True)
class Mission:
    id: str
    source_mission_id: str
    tenant: str
    workspace: str
    priority: int
    dependencies: tuple[str, ...]
    approval_state: ApprovalState
    risk_state: RiskState
    execution_window: ExecutionWindow
    payload: dict[str, Any] = field(default_factory=dict)
    state: MissionState = MissionState.QUEUED
    attempts: int = 0
    max_attempts: int = 3
    worker: str | None = None
    queue: str = "default"
    delegated: dict[str, str] = field(default_factory=dict)
    checkpoint: str | None = None
    failure: str | None = None
    created_at: datetime = field(default_factory=utcnow)
    started_at: datetime | None = None
    finished_at: datetime | None = None

    def validate(self) -> None:
        if not all((self.id, self.source_mission_id, self.tenant, self.workspace)):
            raise ValueError("Mission identity and scope are required.")
        if not 1 <= self.priority <= 5:
            raise ValueError("Priority must be within [1, 5].")
        if self.id in self.dependencies:
            raise ValueError("A mission cannot depend on itself.")
        if self.max_attempts < 1:
            raise ValueError("At least one mission attempt is required.")
        forbidden = {"password", "secret", "token", "cookie", "credential", "session"}
        if forbidden & {key.casefold() for key in self.payload}:
            raise ValueError("Secrets are forbidden in mission payloads.")
        self.execution_window.validate()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Checkpoint:
    mission_id: str
    tenant: str
    workspace: str
    reference: str
    progress: float
    created_at: datetime = field(default_factory=utcnow)


@dataclass(slots=True)
class AuditEntry:
    mission_id: str
    tenant: str
    workspace: str
    actor: str
    action: str
    timestamp: datetime = field(default_factory=utcnow)
