from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..models import CloudValue, snapshot


class DeploymentOutcome(str, Enum):
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class DeploymentIssue:
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class DeploymentArtifactDescriptor:
    name: str
    kind: str


@dataclass(frozen=True, slots=True)
class DeploymentResult:
    deployment_id: str
    outcome: DeploymentOutcome = DeploymentOutcome.UNKNOWN
    issues: tuple[DeploymentIssue, ...] = ()
    artifacts: tuple[DeploymentArtifactDescriptor, ...] = ()
    completed_at: datetime | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        object.__setattr__(self, "metadata", snapshot(self.metadata))
