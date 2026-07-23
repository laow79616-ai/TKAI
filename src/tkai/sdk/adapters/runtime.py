"""Composition-only AgentRuntime adapter for explicitly injected SDK services."""

from __future__ import annotations

from collections.abc import Iterable

from ..agent import AgentRequest, AgentResponse, AgentRuntime
from ..memory import Memory
from .memory import MemoryAdapter
from .providers import ProviderAdapter


class V1RuntimeAdapter(AgentRuntime):
    """Bridge SDK calls to explicit provider/memory adapters without V1.x mutation."""

    def __init__(
        self, provider: ProviderAdapter, *, memory: Memory | None = None
    ) -> None:
        self.provider = provider
        self.memory = MemoryAdapter(memory) if memory is not None else None

    def chat(self, request: AgentRequest) -> AgentResponse:
        """Execute a local provider chat after optional explicit memory injection."""
        return self._annotate(self.provider.chat(self._with_memory(request)), request)

    def run(self, request: AgentRequest) -> AgentResponse:
        """Run currently maps to the same explicit provider path as chat."""
        return self.chat(request)

    def stream(self, request: AgentRequest) -> Iterable[AgentResponse]:
        """Yield provider responses without threads, buffering, or implicit cleanup."""
        enriched = self._with_memory(request)
        return (
            self._annotate(response, request)
            for response in self.provider.stream(enriched)
        )

    def call(self, name: str, request: AgentRequest) -> AgentResponse:
        """Execute a named provider capability with optional memory injection."""
        return self._annotate(
            self.provider.call(name, self._with_memory(request)), request
        )

    def _with_memory(self, request: AgentRequest) -> AgentRequest:
        if self.memory is None:
            return request
        key = request.options.get("memory_key")
        if not isinstance(key, str):
            return request
        value = self.memory.context(key)
        if value is None:
            return request
        return AgentRequest(request.input, {**request.options, "memory": value})

    @staticmethod
    def _annotate(response: AgentResponse, request: AgentRequest) -> AgentResponse:
        memory_key = request.options.get("memory_key")
        metadata = dict(response.metadata)
        if isinstance(memory_key, str):
            metadata["memory_key"] = memory_key
        return AgentResponse(response.output, metadata)
