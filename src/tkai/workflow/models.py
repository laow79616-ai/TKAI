"""Typed workflow domain models and validated lifecycle transitions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from typing import Any


class WorkflowStatus(Enum):
    CREATED = auto()
    VALIDATED = auto()
    PENDING = auto()
    RUNNING = auto()
    PAUSED = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


class StepStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    SKIPPED = auto()
    COMPLETED = auto()
    FAILED = auto()


@dataclass(slots=True)
class WorkflowDefinition:
    name: str
    steps: list[Any]
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class WorkflowContext:
    inputs: dict[str, Any] = field(default_factory=dict)
    shared: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    previous_result: Any = None

    def data(self) -> dict[str, Any]:
        return {
            **self.inputs,
            **self.shared,
            "results": self.results,
            "previous_result": self.previous_result,
        }


@dataclass(slots=True)
class StepResult:
    name: str
    status: StepStatus
    output: Any = None
    error: Exception | None = None
    attempts: int = 0


@dataclass(slots=True)
class WorkflowResult:
    name: str
    status: WorkflowStatus
    steps: list[StepResult] = field(default_factory=list)
    output: Any = None
    error: Exception | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.name
        for item in data["steps"]:
            item["status"] = item["status"].name
            item["error"] = str(item["error"]) if item["error"] else None
        data["error"] = str(self.error) if self.error else None
        return data


class Workflow:
    _TRANSITIONS = {
        WorkflowStatus.CREATED: {WorkflowStatus.VALIDATED, WorkflowStatus.CANCELLED},
        WorkflowStatus.VALIDATED: {WorkflowStatus.PENDING, WorkflowStatus.CANCELLED},
        WorkflowStatus.PENDING: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
        WorkflowStatus.RUNNING: {
            WorkflowStatus.PAUSED,
            WorkflowStatus.COMPLETED,
            WorkflowStatus.FAILED,
            WorkflowStatus.CANCELLED,
        },
        WorkflowStatus.PAUSED: {WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED},
        WorkflowStatus.COMPLETED: set(),
        WorkflowStatus.FAILED: set(),
        WorkflowStatus.CANCELLED: set(),
    }

    def __init__(self, definition: WorkflowDefinition) -> None:
        self.definition = definition
        self.status = WorkflowStatus.CREATED

    def transition(self, status: WorkflowStatus) -> None:
        if status not in self._TRANSITIONS[self.status]:
            raise ValueError(
                f"Illegal workflow transition: {self.status.name} -> {status.name}"
            )
        self.status = status

    def pause(self) -> None:
        self.transition(WorkflowStatus.PAUSED)

    def resume(self) -> None:
        self.transition(WorkflowStatus.RUNNING)

    def cancel(self) -> None:
        self.transition(WorkflowStatus.CANCELLED)

    def checkpoint(self) -> bool:
        """Return whether cooperative scheduling may start another step."""
        return self.status is WorkflowStatus.RUNNING

    def snapshot(
        self, context: WorkflowContext, result: WorkflowResult
    ) -> dict[str, Any]:
        """Return an in-memory recovery payload."""
        return {
            "status": self.status.name,
            "context": {
                "inputs": context.inputs,
                "shared": context.shared,
                "results": context.results,
                "previous_result": context.previous_result,
            },
            "result": result.to_dict(),
        }
