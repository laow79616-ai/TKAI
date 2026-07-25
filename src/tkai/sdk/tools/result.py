"""Immutable results for synchronous, cancellation-aware reference Tool calls."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


class ToolStatus(str, Enum):
    """Reference execution states without transport or external service semantics."""

    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


@dataclass(frozen=True, slots=True)
class ToolResult:
    """A safe output or concise error result from one local tool invocation."""

    status: ToolStatus
    output: object | None = None
    error: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
