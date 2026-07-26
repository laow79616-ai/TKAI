"""Domain models for enterprise reasoning sessions and artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class ReasoningMode(str, Enum):
    PLANNING = "planning"
    DECISION = "decision"
    CHAIN = "chain"
    TREE = "tree"
    REFLECTION = "reflection"
    CRITIQUE = "critique"
    SIMULATION = "simulation"
    OPTIMIZATION = "optimization"
    DELEGATION = "delegation"


class LifecycleState(str, Enum):
    CREATED = "created"
    PREPARED = "prepared"
    RUNNING = "running"
    VALIDATED = "validated"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class ReasoningScope:
    tenant: str
    workspace: str
    actor: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.workspace or not self.actor:
            raise ValueError("Tenant, workspace, and actor are required.")


@dataclass(slots=True)
class ReasoningSession:
    id: str
    tenant: str
    workspace: str
    agent: str
    goal: str
    strategy: str
    mode: ReasoningMode
    state: LifecycleState = LifecycleState.CREATED
    priority: int = 50
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["mode"] = self.mode.value
        value["state"] = self.state.value
        value["created_at"] = self.created_at.isoformat()
        value["updated_at"] = self.updated_at.isoformat()
        return value


@dataclass(frozen=True, slots=True)
class PlanTask:
    id: str
    goal: str
    dependencies: tuple[str, ...] = ()
    priority: int = 50

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "goal": self.goal,
            "dependencies": list(self.dependencies),
            "priority": self.priority,
        }


@dataclass(frozen=True, slots=True)
class ExecutionPlan:
    goal: str
    subtasks: tuple[PlanTask, ...]
    execution_order: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "subtasks": [task.to_dict() for task in self.subtasks],
            "dependencies": {
                task.id: list(task.dependencies) for task in self.subtasks
            },
            "execution_plan": list(self.execution_order),
        }


@dataclass(frozen=True, slots=True)
class Decision:
    option: str
    score: float
    confidence: float
    fallback: str | None
    ranking: tuple[tuple[str, float], ...]
    rules: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "option": self.option,
            "score": self.score,
            "confidence": self.confidence,
            "fallback": self.fallback,
            "ranking": [
                {"option": item, "score": score} for item, score in self.ranking
            ],
            "rules": list(self.rules),
        }


@dataclass(frozen=True, slots=True)
class ValidationResult:
    valid: bool
    failures: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SimulationResult:
    scenario: str
    prediction: dict[str, Any]
    evaluation: float
    comparison: dict[str, float]
    rollback_plan: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["rollback_plan"] = list(self.rollback_plan)
        return value


@dataclass(frozen=True, slots=True)
class OptimizationResult:
    resource: dict[str, float]
    execution: tuple[str, ...]
    estimated_cost: float
    estimated_latency: float

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["execution"] = list(self.execution)
        return value
