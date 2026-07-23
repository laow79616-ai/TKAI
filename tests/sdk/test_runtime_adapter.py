"""Explicit adapter delegation and dependency-injection coverage."""

from __future__ import annotations

import pytest

from tkai.sdk import AgentRequest
from tkai.sdk.adapters import InMemoryProvider, ProviderAdapter, V1RuntimeAdapter
from tkai.sdk.errors import AdapterError


def test_runtime_adapter_delegates_without_creating_a_provider_manager() -> None:
    """The exact injected reference provider supplies every response."""
    provider = InMemoryProvider("reference", responder=lambda request: request.input)
    adapter = V1RuntimeAdapter(ProviderAdapter(provider))

    assert adapter.chat(AgentRequest("chat")).metadata["provider"] == "reference"
    assert adapter.run(AgentRequest("run")).output == "run"
    assert adapter.call("echo", AgentRequest("call")).metadata["call"] == "echo"


def test_provider_adapter_rejects_named_calls_not_offered_by_dependency() -> None:
    """A missing explicit capability is a stable adapter error without fallback."""

    class ChatOnlyProvider:
        descriptor = InMemoryProvider().descriptor

        def chat(self, request: AgentRequest):
            return InMemoryProvider().chat(request)

        def stream(self, request: AgentRequest):
            return InMemoryProvider().stream(request)

        def close(self) -> None:
            return None

    with pytest.raises(AdapterError):
        ProviderAdapter(ChatOnlyProvider()).call("missing", AgentRequest("input"))
