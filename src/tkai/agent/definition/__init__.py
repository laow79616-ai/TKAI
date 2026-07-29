"""Immutable enterprise agent definitions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from ..models import AgentLimits, immutable_mapping


@dataclass(frozen=True, slots=True)
class AgentDefinition:
    agent_id: str
    name: str
    description: str
    version: str
    prompt: str
    tools: tuple[str, ...] = ()
    memory: tuple[str, ...] = ()
    permissions: tuple[str, ...] = ()
    limits: AgentLimits = AgentLimits()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not all((self.agent_id, self.name, self.version, self.prompt)):
            raise ValueError("Agent id, name, version, and prompt are required.")
        object.__setattr__(self, "tools", tuple(dict.fromkeys(self.tools)))
        object.__setattr__(self, "memory", tuple(dict.fromkeys(self.memory)))
        object.__setattr__(self, "permissions", tuple(sorted(set(self.permissions))))
        object.__setattr__(self, "metadata", immutable_mapping(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "prompt": self.prompt,
            "tools": list(self.tools),
            "memory": list(self.memory),
            "permissions": list(self.permissions),
            "limits": {
                "max_steps": self.limits.max_steps,
                "timeout_seconds": self.limits.timeout_seconds,
                "max_tool_calls": self.limits.max_tool_calls,
            },
            "metadata": dict(self.metadata),
        }
