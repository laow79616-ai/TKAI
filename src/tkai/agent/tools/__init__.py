"""Permission-aware local tool registry."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from threading import RLock
from typing import Any

from ..models import immutable_mapping


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    attempts: int = 1

    def __post_init__(self) -> None:
        if self.attempts < 1:
            raise ValueError("Retry attempts must be positive.")


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    name: str
    schema: Mapping[str, Any]
    permission: str
    timeout_seconds: float = 30.0
    retry: RetryPolicy = RetryPolicy()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name or not self.permission or self.timeout_seconds <= 0:
            raise ValueError("Tool name, permission, and timeout are required.")
        object.__setattr__(self, "schema", immutable_mapping(self.schema))
        object.__setattr__(self, "metadata", immutable_mapping(self.metadata))


@dataclass(frozen=True, slots=True)
class RegisteredTool:
    definition: ToolDefinition
    handler: Callable[[Mapping[str, Any]], Any] = field(repr=False, compare=False)


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}
        self._lock = RLock()

    def register(self, tool: RegisteredTool) -> None:
        with self._lock:
            if tool.definition.name in self._tools:
                raise ValueError(f"Tool '{tool.definition.name}' already exists.")
            self._tools[tool.definition.name] = tool

    def get(self, name: str, permissions: tuple[str, ...]) -> RegisteredTool:
        with self._lock:
            tool = self._tools.get(name)
            if tool is None:
                raise KeyError(name)
            if tool.definition.permission not in permissions:
                raise PermissionError(
                    f"Permission '{tool.definition.permission}' is required."
                )
            return tool

    def list(self) -> tuple[ToolDefinition, ...]:
        with self._lock:
            return tuple(self._tools[name].definition for name in sorted(self._tools))
