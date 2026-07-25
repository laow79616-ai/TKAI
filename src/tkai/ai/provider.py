"""Unified AI provider abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import replace
from typing import Any

from tkai.core.exceptions import AIProviderError

from .errors import ProviderConfigurationError
from .models import (
    AIRequest,
    AIResponse,
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
    ProviderCapabilities,
)

CompletionClient = Callable[[AIRequest], AIResponse | str]


class AIProvider(ABC):
    """Common interface implemented by every supported AI provider."""

    name: str
    default_model: str

    @abstractmethod
    def generate(
        self, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        """Generate a response for ``prompt``."""

    def initialize(self) -> None:
        """Initialize optional provider resources."""
        return None

    def validate_config(self) -> None:
        """Validate provider configuration before invocation."""
        return None

    def list_models(self) -> list[ModelInfo]:
        """List models known to this provider."""
        return []

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Execute a normalized chat request."""
        raise ProviderConfigurationError(
            f"Provider '{self.name}' does not support chat"
        )

    def stream_chat(self, request: ChatRequest) -> Iterator[ChatResponse]:
        """Yield normalized streaming response increments."""
        raise ProviderConfigurationError(
            f"Provider '{self.name}' does not support streaming"
        )

    async def astream_chat(self, request: ChatRequest) -> AsyncIterator[ChatResponse]:
        """Expose synchronous streaming via an async iterator."""
        for response in self.stream_chat(request):
            yield response

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Create normalized embeddings."""
        raise ProviderConfigurationError(
            f"Provider '{self.name}' does not support embeddings"
        )

    def health_check(self) -> bool:
        """Return whether local configuration is usable."""
        try:
            self.validate_config()
        except ProviderConfigurationError:
            return False
        return True

    def close(self) -> None:
        """Close optional resources."""
        return None


class BaseAIProvider(AIProvider):
    """Provider base class that delegates transport to an injected client."""

    name = "base"
    default_model = ""
    capabilities = ProviderCapabilities()

    def __init__(self, client: CompletionClient | None = None) -> None:
        self.client = client

    def generate(
        self, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        """Normalize the injected client's result into an :class:`AIResponse`."""
        if self.client is None:
            raise AIProviderError(
                f"Provider '{self.name}' requires a configured completion client"
            )
        selected_model = model or self.default_model
        request = AIRequest(prompt=prompt, model=selected_model, options=options)
        response = self.client(request)
        if isinstance(response, str):
            return AIResponse(response, self.name, selected_model, response)
        return replace(
            response,
            provider=self.name,
            model=response.model or selected_model,
        )
