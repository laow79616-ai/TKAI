"""Immutable agent run records."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from typing import Any

from ..models import AgentEvent, AgentStatus, RunMetrics, immutable_mapping


@dataclass(frozen=True, slots=True)
class AgentRun:
    run_id: str
    agent_id: str
    workspace: str
    inputs: Mapping[str, Any] = field(default_factory=dict)
    outputs: Mapping[str, Any] = field(default_factory=dict)
    status: AgentStatus = AgentStatus.CREATED
    events: tuple[AgentEvent, ...] = ()
    metrics: RunMetrics = RunMetrics()

    def __post_init__(self) -> None:
        if not self.run_id or not self.agent_id or not self.workspace:
            raise ValueError("Run id, agent id, and workspace are required.")
        object.__setattr__(self, "inputs", immutable_mapping(self.inputs))
        object.__setattr__(self, "outputs", immutable_mapping(self.outputs))

    def evolve(self, **changes: Any) -> AgentRun:
        return replace(self, **changes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "workspace": self.workspace,
            "inputs": dict(self.inputs),
            "outputs": dict(self.outputs),
            "status": self.status.value,
            "events": [event.to_dict() for event in self.events],
            "metrics": self.metrics.to_dict(),
        }

