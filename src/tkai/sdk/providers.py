"""Provider SDK contracts independent of concrete V1.x provider adapters."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from .agent import AgentRequest, AgentResponse


class ProviderCapability(str, Enum):
    """Shared capability names for SDK provider declarations."""

    CHAT = "chat"
    STREAMING = "streaming"
    EMBEDDINGS = "embeddings"
    TOOLS = "tools"


@dataclass(frozen=True, slots=True)
class ProviderDescriptor:
    """Immutable provider metadata consumed by future SDK adapters."""

    name: str
    capabilities: frozenset[ProviderCapability] = frozenset()


class Provider(Protocol):
    """Unified synchronous provider contract for SDK-to-runtime adapters."""

    @property
    def descriptor(self) -> ProviderDescriptor: ...
    def chat(self, request: AgentRequest) -> AgentResponse: ...
    def stream(self, request: AgentRequest) -> Iterable[AgentResponse]: ...
    def close(self) -> None: ...
