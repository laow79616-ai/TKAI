"""Typed execution-plan and runtime models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Priority(int, Enum):
    LOW = 10
    NORMAL = 50
    HIGH = 80
    CRITICAL = 100


class RouteType(str, Enum):
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    WORKFLOW = "workflow"
    KNOWLEDGE = "knowledge"
    TOOL = "tool"
    PLUGIN = "plugin"
    APPLICATION = "application"


class ExecutionState(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ROLLED_BACK = "rolled_back"
    DEAD_LETTER = "dead_letter"


@dataclass(frozen=True, slots=True)
class Scope:
    tenant: str
    actor: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.actor:
            raise ValueError("Tenant and actor are required.")


@dataclass(frozen=True, slots=True)
class PlanStep:
    id: str
    name: str
    route: RouteType
    target: str
    dependencies: tuple[str, ...] = ()
    condition: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    id: str
    name: str
    description: str
    priority: Priority
    dependencies: tuple[str, ...]
    state: ExecutionState
    metadata: dict[str, Any]
    scope: Scope
    steps: tuple[PlanStep, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Execution:
    id: str
    plan_id: str
    scope: Scope
    state: ExecutionState = ExecutionState.PENDING
    results: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    attempts: int = 0
    checkpoint_id: str | None = None
    cancelled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
