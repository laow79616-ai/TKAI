from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..models import CloudValue, snapshot


class ExecutionOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ExecutionMetadata:
    values: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", snapshot(self.values))


@dataclass(frozen=True, slots=True)
class ExecutionDescriptor:
    execution_id: str
    deployment_id: str
    project_id: str
    workspace_id: str
    status: object
    outcome: ExecutionOutcome = ExecutionOutcome.UNKNOWN
    started_at: datetime | None = None
    finished_at: datetime | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not all(
            (self.execution_id, self.deployment_id, self.project_id, self.workspace_id)
        ):
            raise ValueError("Execution identifiers are required.")
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    execution_id: str
    outcome: ExecutionOutcome = ExecutionOutcome.UNKNOWN
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))
