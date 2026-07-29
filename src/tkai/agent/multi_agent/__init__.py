"""Bounded role-based multi-agent coordination contracts."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Any


class AgentRole(str, Enum):
    PLANNER = "planner"
    RESEARCH = "research"
    CODER = "coder"
    REVIEWER = "reviewer"
    EXECUTOR = "executor"
    SUPPORT = "support"


@dataclass(frozen=True, slots=True)
class CoordinationLimits:
    maximum_depth: int = 3
    maximum_agents: int = 8
    timeout_seconds: float = 300.0

    def __post_init__(self) -> None:
        if min(self.maximum_depth, self.maximum_agents, self.timeout_seconds) <= 0:
            raise ValueError("Coordinator limits must be positive.")


@dataclass(frozen=True, slots=True)
class Delegation:
    source_agent_id: str
    target_agent_id: str
    role: AgentRole
    task: Mapping[str, Any] = field(default_factory=dict)
    depth: int = 1


@dataclass(frozen=True, slots=True)
class Aggregation:
    outputs: tuple[Any, ...]
    cancelled: bool = False


class AgentCoordinator:
    """Validates delegation bounds; callers provide the execution mechanism."""

    def __init__(self, limits: CoordinationLimits | None = None) -> None:
        self.limits = limits or CoordinationLimits()

    def coordinate(
        self,
        delegations: Sequence[Delegation],
        execute: Callable[[Delegation], Any],
        *,
        cancelled: Callable[[], bool] = lambda: False,
    ) -> Aggregation:
        if len(delegations) > self.limits.maximum_agents:
            raise ValueError("Maximum agents exceeded.")
        if any(item.depth > self.limits.maximum_depth for item in delegations):
            raise ValueError("Maximum delegation depth exceeded.")
        outputs: list[Any] = []
        started = monotonic()
        for item in delegations:
            if cancelled():
                return Aggregation(tuple(outputs), cancelled=True)
            if monotonic() - started > self.limits.timeout_seconds:
                raise TimeoutError("Multi-agent coordination timed out.")
            outputs.append(execute(item))
        return Aggregation(tuple(outputs))
