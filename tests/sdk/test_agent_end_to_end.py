"""Offline Agent-to-adapter-to-reference-provider coverage."""

from __future__ import annotations

import pytest

from tkai.sdk import Agent, AgentRequest, AgentResponse, MemoryRecord
from tkai.sdk.adapters import (
    InMemoryMemory,
    InMemoryProvider,
    ProviderAdapter,
    V1RuntimeAdapter,
)
from tkai.sdk.errors import InvalidRequestError, ProviderExecutionError


def runtime_with_memory() -> V1RuntimeAdapter:
    """Build an explicit local dependency graph without providers or configuration."""
    memory = InMemoryMemory()
    memory.put(MemoryRecord("session", "remembered"))
    provider = InMemoryProvider(
        responder=lambda request: f"{request.input}:{request.options.get('memory', '')}"
    )
    return V1RuntimeAdapter(ProviderAdapter(provider), memory=memory)


def test_agent_chat_run_call_and_stream_use_explicit_local_dependencies() -> None:
    """All public Agent paths are deterministic and never invoke external services."""
    agent = Agent(runtime_with_memory())

    assert agent.chat("chat", memory_key="session").output == "chat:remembered"
    assert agent.run("run").output == "run:"
    assert agent.call("echo", "call").metadata["call"] == "echo"
    assert [item.output for item in agent.stream("stream")] == ["stream:"]


def test_invalid_requests_and_provider_failures_preserve_clear_sdk_errors() -> None:
    """Validation occurs before provider work and provider causes remain inspectable."""
    agent = Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider())))
    with pytest.raises(InvalidRequestError):
        agent.chat(None)

    def fail(_request: object) -> object:
        raise RuntimeError("provider failure")

    failing = Agent(V1RuntimeAdapter(ProviderAdapter(InMemoryProvider(responder=fail))))
    with pytest.raises(ProviderExecutionError) as caught:
        failing.chat("fail")
    assert isinstance(caught.value.__cause__, RuntimeError)

    with pytest.raises(ProviderExecutionError) as streamed:
        list(failing.stream("fail"))
    assert isinstance(streamed.value.__cause__, RuntimeError)


def test_early_stream_close_propagates_to_the_upstream_local_generator() -> None:
    """Closing an Agent stream closes the injected provider iterator without threads."""
    closed = False

    class ClosingProvider(InMemoryProvider):
        def stream(self, request: AgentRequest):
            nonlocal closed
            try:
                yield AgentResponse(request.input)
                yield AgentResponse("not consumed")
            finally:
                closed = True

    agent = Agent(V1RuntimeAdapter(ProviderAdapter(ClosingProvider())))
    stream = iter(agent.stream("one"))
    assert next(stream).output == "one"
    stream.close()
    assert closed
