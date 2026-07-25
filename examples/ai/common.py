"""Shared deterministic provider used by the offline AI examples."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from typing import Any

from tkai.ai import (
    AIResponse,
    BaseAIProvider,
    ChatRequest,
    ChatResponse,
    ProviderCapabilities,
)


class ExampleProvider(BaseAIProvider):
    """Small no-network provider that exercises public manager interfaces."""

    capabilities = ProviderCapabilities(
        chat=True, streaming=True, tools=True, async_=True
    )

    def __init__(self, name: str = "example") -> None:
        super().__init__()
        self.name = name
        self.default_model = f"{name}-model"

    def generate(
        self, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        """Return a deterministic legacy-compatible completion response."""
        return AIResponse(prompt, self.name, model or self.default_model)

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Return a deterministic normalized chat response."""
        return ChatResponse(
            content=f"{self.name}:ok",
            provider=self.name,
            model=request.model or self.default_model,
        )

    async def achat(self, request: ChatRequest) -> ChatResponse:
        """Return the asynchronous form of :meth:`chat`."""
        return self.chat(request)

    def stream_chat(self, request: ChatRequest) -> Iterator[ChatResponse]:
        """Yield one deterministic stream item."""
        yield self.chat(request)

    async def astream_chat(self, request: ChatRequest) -> AsyncIterator[ChatResponse]:
        """Yield one asynchronous deterministic stream item."""
        yield self.chat(request)
