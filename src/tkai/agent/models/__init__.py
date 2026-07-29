"""Shared immutable agent runtime models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Any


def immutable_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a shallow, deterministic immutable copy."""
    return MappingProxyType(dict(sorted(value.items())))


class AgentStatus(str, Enum):
    DRAFT = "draft"
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class AgentLimits:
    max_steps: int = 100
    timeout_seconds: float = 300.0
    max_tool_calls: int = 50

    def __post_init__(self) -> None:
        if min(self.max_steps, self.timeout_seconds, self.max_tool_calls) <= 0:
            raise ValueError("Agent limits must be positive.")


@dataclass(frozen=True, slots=True)
class AgentEvent:
    sequence: int
    action: str
    status: AgentStatus
    timestamp: str
    detail: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "detail", immutable_mapping(self.detail))

    def to_dict(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "action": self.action,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "detail": dict(self.detail),
        }


@dataclass(frozen=True, slots=True)
class RunMetrics:
    duration_seconds: float = 0.0
    tool_calls: int = 0
    tool_failures: int = 0

    def to_dict(self) -> dict[str, int | float]:
        return {
            "duration_seconds": self.duration_seconds,
            "tool_calls": self.tool_calls,
            "tool_failures": self.tool_failures,
        }
