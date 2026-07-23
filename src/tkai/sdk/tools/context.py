"""Explicit context and request values for synchronous reference Tool execution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from threading import Event
from types import MappingProxyType


@dataclass(slots=True)
class ToolContext:
    """Caller-supplied dependencies, cancellation event, and local metadata."""

    memory: object | None = None
    provider: object | None = None
    agent: object | None = None
    cancellation: Event = field(default_factory=Event)
    timeout_seconds: float | None = None
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ToolRequest:
    """One immutable named invocation with an explicitly supplied context."""

    name: str
    arguments: Mapping[str, object] = field(default_factory=dict)
    context: ToolContext = field(default_factory=ToolContext)

    def __post_init__(self) -> None:
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))
