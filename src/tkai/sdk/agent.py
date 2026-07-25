"""Developer Agent facade that delegates all execution to a runtime adapter."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import NoReturn, Protocol

from .errors import SDKConfigurationError


@dataclass(frozen=True, slots=True)
class AgentRequest:
    """Runtime-neutral request payload passed to a V1.x-compatible adapter."""

    input: object
    options: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AgentResponse:
    """Runtime-neutral response returned by an SDK adapter."""

    output: object
    metadata: Mapping[str, object] = field(default_factory=dict)


class AgentRuntime(Protocol):
    """Small contract that bridges SDK calls onto an existing runtime."""

    def chat(self, request: AgentRequest) -> AgentResponse: ...
    def run(self, request: AgentRequest) -> AgentResponse: ...
    def stream(self, request: AgentRequest) -> Iterable[AgentResponse]: ...
    def call(self, name: str, request: AgentRequest) -> AgentResponse: ...


class _UnconfiguredRuntime:
    """Safe default that avoids hidden provider or workflow execution."""

    @staticmethod
    def _raise() -> NoReturn:
        raise SDKConfigurationError("Agent requires an explicit AgentRuntime adapter.")

    def chat(self, request: AgentRequest) -> AgentResponse:
        del request
        self._raise()

    def run(self, request: AgentRequest) -> AgentResponse:
        del request
        self._raise()

    def stream(self, request: AgentRequest) -> Iterable[AgentResponse]:
        del request
        self._raise()
        return ()

    def call(self, name: str, request: AgentRequest) -> AgentResponse:
        del name, request
        self._raise()


class Agent:
    """Stable SDK facade for chat, task, stream, and named-call interactions."""

    def __init__(self, runtime: AgentRuntime | None = None) -> None:
        self.runtime: AgentRuntime = runtime or _UnconfiguredRuntime()

    def chat(self, message: object, **options: object) -> AgentResponse:
        """Delegate one conversation request to the configured runtime."""
        return self.runtime.chat(AgentRequest(message, options))

    def run(self, task: object, **options: object) -> AgentResponse:
        """Delegate one task request to the configured runtime."""
        return self.runtime.run(AgentRequest(task, options))

    def stream(self, input: object, **options: object) -> Iterable[AgentResponse]:
        """Return the runtime's streaming iterable without buffering it."""
        return self.runtime.stream(AgentRequest(input, options))

    def call(self, name: str, input: object, **options: object) -> AgentResponse:
        """Delegate a named capability call to the configured runtime."""
        return self.runtime.call(name, AgentRequest(input, options))
