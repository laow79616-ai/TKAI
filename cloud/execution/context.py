from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from ..models import CloudValue, snapshot


@dataclass(frozen=True, slots=True)
class ExecutionContext:
    execution_id: str | None = None
    deployment_id: str | None = None
    project_id: str | None = None
    workspace_id: str | None = None
    request_id: str | None = None
    correlation_id: str | None = None
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "execution_id": self.execution_id,
            "deployment_id": self.deployment_id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "request_id": self.request_id,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }
