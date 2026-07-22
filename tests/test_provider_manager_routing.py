"""Offline routing and lifecycle coverage for :class:`ProviderManager`."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest

from tkai.ai import (
    AIResponse,
    BaseAIProvider,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ProviderManager,
    ProviderNotFoundError,
)


class RoutingProvider(BaseAIProvider):
    """Offline provider that records all normalized manager calls."""

    def __init__(self, name: str) -> None:
        super().__init__()
        self.name = name
        self.default_model = f"{name}-default"
        self.calls: list[tuple[str, str | None]] = []
        self.closed = False
        self.async_closed = False

    def generate(
        self, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        return AIResponse(prompt, self.name, model or self.default_model)

    def chat(self, request: ChatRequest) -> ChatResponse:
        self.calls.append(("chat", request.model))
        return self._response(request)

    async def achat(self, request: ChatRequest) -> ChatResponse:
        self.calls.append(("achat", request.model))
        return self._response(request)

    def stream_chat(self, request: ChatRequest) -> Iterator[ChatResponse]:
        self.calls.append(("stream", request.model))
        yield self._response(request)

    async def astream_chat(self, request: ChatRequest) -> AsyncIterator[ChatResponse]:
        self.calls.append(("astream", request.model))
        yield self._response(request)

    def _response(self, request: ChatRequest) -> ChatResponse:
        """Build the common normalized response used by this test double."""
        return ChatResponse(
            content=self.name,
            provider=self.name,
            model=request.model or "",
        )

    def close(self) -> None:
        self.closed = True

    async def aclose(self) -> None:
        self.async_closed = True


def request(model: str | None = None) -> ChatRequest:
    """Create a simple request with an optional routeable model name."""
    return ChatRequest((ChatMessage("user", "hello"),), model=model)


def test_registry_default_lookup_and_alias_routing() -> None:
    manager = ProviderManager()
    primary = RoutingProvider("primary")
    manager.register(primary, default=True, aliases=("main",))

    assert manager.names() == ["primary"]
    assert manager.aliases() == {"main": "primary"}
    assert manager.get("main") is primary
    assert manager.chat(request()).provider == "primary"
    assert manager.chat(request(), provider="main").provider == "primary"


def test_provider_prefixed_model_routes_and_preserves_multi_segment_suffix() -> None:
    manager = ProviderManager()
    primary = RoutingProvider("primary")
    manager.register(primary, aliases=("openrouter",))

    response = manager.chat(request(), model="openrouter/anthropic/claude-test")

    assert response.provider == "primary"
    assert primary.calls == [("chat", "anthropic/claude-test")]


def test_unknown_explicit_provider_never_uses_default() -> None:
    manager = ProviderManager()
    manager.register(RoutingProvider("primary"), default=True)

    with pytest.raises(ProviderNotFoundError, match="missing"):
        manager.chat(request(), provider="missing")


def test_sync_stream_routing() -> None:
    manager = ProviderManager()
    provider = RoutingProvider("primary")
    manager.register(provider, default=True)

    assert [item.content for item in manager.stream_chat(request("model"))] == [
        "primary"
    ]
    assert provider.calls == [("stream", "model")]


def test_async_routing_and_lifecycle() -> None:
    async def run() -> None:
        manager = ProviderManager()
        provider = RoutingProvider("primary")
        manager.register(provider, default=True)

        assert (await manager.achat(request("model"))).provider == "primary"
        result = [item.content async for item in manager.astream_chat(request("model"))]
        assert result == ["primary"]
        await manager.aclose()
        await manager.aclose()
        assert provider.async_closed
        assert manager.names() == []

    asyncio.run(run())


def test_sync_close_unregisters_each_provider_once() -> None:
    manager = ProviderManager()
    first = RoutingProvider("first")
    second = RoutingProvider("second")
    manager.register(first, default=True)
    manager.register(second)

    manager.close()
    manager.close()

    assert first.closed and second.closed
    assert manager.names() == []
