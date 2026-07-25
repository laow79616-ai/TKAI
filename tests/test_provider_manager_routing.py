"""Offline routing and lifecycle coverage for :class:`ProviderManager`."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Iterator
from typing import Any

import pytest

from tkai.ai import (
    AIResponse,
    BaseAIProvider,
    Capability,
    CapabilityNotSupportedError,
    ChatMessage,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    NoCapableProviderError,
    ProviderCapabilities,
    ProviderManager,
    ProviderNotFoundError,
)


class RoutingProvider(BaseAIProvider):
    """Offline provider that records all normalized manager calls."""

    def __init__(
        self, name: str, capabilities: ProviderCapabilities | None = None
    ) -> None:
        super().__init__()
        self.name = name
        self.default_model = f"{name}-default"
        self.capabilities = capabilities or ProviderCapabilities()
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

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        self.calls.append(("embed", request.model))
        return EmbeddingResponse(
            embeddings=((1.0,),),
            model=request.model or "",
            provider=self.name,
        )


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


def test_empty_capability_request_preserves_default_routing() -> None:
    manager = ProviderManager()
    manager.register(RoutingProvider("backup"))
    manager.register(RoutingProvider("primary"), default=True)

    assert manager.chat(request()).provider == "primary"


def test_explicit_provider_must_support_every_required_capability() -> None:
    manager = ProviderManager()
    manager.register(
        RoutingProvider("primary", ProviderCapabilities(chat=True, tools=True)),
        default=True,
    )

    assert (
        manager.chat(
            request(), provider="primary", required_capabilities=(Capability.TOOLS,)
        ).provider
        == "primary"
    )
    with pytest.raises(CapabilityNotSupportedError, match="vision"):
        manager.chat(
            request(), provider="primary", required_capabilities=(Capability.VISION,)
        )


def test_alias_and_prefixed_model_validate_capabilities() -> None:
    manager = ProviderManager()
    provider = RoutingProvider("primary")
    manager.register(
        provider,
        aliases=("openrouter",),
        model_capabilities={
            "vision-model": ProviderCapabilities(chat=True, vision=True),
        },
    )

    assert (
        manager.chat(
            request(),
            model="openrouter/vision-model",
            required_capabilities=(Capability.VISION,),
        ).provider
        == "primary"
    )
    assert provider.calls == [("chat", "vision-model")]
    with pytest.raises(CapabilityNotSupportedError, match="vision"):
        manager.chat(
            request(), provider="openrouter", required_capabilities=(Capability.VISION,)
        )


def test_model_capability_override_can_add_or_remove_provider_capabilities() -> None:
    manager = ProviderManager()
    manager.register(
        RoutingProvider("primary"),
        default=True,
        capabilities=ProviderCapabilities(chat=True, streaming=True),
        model_capabilities={
            "vision-model": ProviderCapabilities(chat=True, vision=True),
        },
    )

    assert manager.model_capabilities("primary")["vision-model"].vision
    with pytest.raises(NoCapableProviderError, match="streaming"):
        list(
            manager.stream_chat(
                request("vision-model"),
                required_capabilities=(Capability.STREAMING,),
            )
        )
    assert (
        manager.chat(
            request("vision-model"), required_capabilities=(Capability.VISION,)
        ).provider
        == "primary"
    )


def test_multi_capability_routing_uses_stable_default_first_order() -> None:
    manager = ProviderManager()
    manager.register(
        RoutingProvider("alpha", ProviderCapabilities(chat=True, tools=True)),
    )
    manager.register(
        RoutingProvider("default", ProviderCapabilities(chat=True, tools=True)),
        default=True,
    )
    manager.register(
        RoutingProvider("zulu", ProviderCapabilities(chat=True, tools=True)),
    )

    response = manager.chat(
        request(), required_capabilities=(Capability.CHAT, Capability.TOOLS)
    )
    assert response.provider == "default"


def test_no_capable_provider_reports_requirements_candidates_and_reasons() -> None:
    manager = ProviderManager()
    manager.register(RoutingProvider("primary"), default=True)
    manager.register(RoutingProvider("backup", ProviderCapabilities(chat=False)))

    with pytest.raises(NoCapableProviderError) as error:
        manager.chat(request(), required_capabilities=(Capability.TOOLS,))

    message = str(error.value)
    assert "tools" in message
    assert "primary" in message
    assert "backup" in message
    assert "missing" in message


def test_capability_routing_is_shared_by_async_and_streaming_calls() -> None:
    async def run() -> None:
        capabilities = ProviderCapabilities(chat=True, streaming=True, async_=True)
        manager = ProviderManager()
        provider = RoutingProvider("primary", capabilities)
        manager.register(provider, default=True)

        assert (
            await manager.achat(request(), required_capabilities=(Capability.ASYNC,))
        ).provider == "primary"
        assert [
            response.content
            async for response in manager.astream_chat(
                request(), required_capabilities=(Capability.ASYNC,)
            )
        ] == ["primary"]
        assert [
            response.content
            for response in manager.stream_chat(
                request(), required_capabilities=(Capability.ASYNC,)
            )
        ] == ["primary"]

    asyncio.run(run())


def test_embeddings_require_explicit_embedding_capability() -> None:
    manager = ProviderManager()
    manager.register(
        RoutingProvider("primary", ProviderCapabilities(chat=True, embeddings=True)),
        default=True,
        model_capabilities={"other": ProviderCapabilities(chat=True)},
    )

    assert (
        manager.embed(
            EmbeddingRequest(("hello",), "embed"),
            required_capabilities=(Capability.EMBEDDINGS,),
        ).provider
        == "primary"
    )
    with pytest.raises(CapabilityNotSupportedError, match="embeddings"):
        manager.embed(
            EmbeddingRequest(("hello",)),
            provider="primary",
            model="other",
            required_capabilities=(Capability.EMBEDDINGS,),
        )
