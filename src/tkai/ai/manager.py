"""Lifecycle and routing facade for registered AI providers."""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import AsyncIterator, Awaitable, Iterable, Iterator
from dataclasses import replace
from threading import RLock
from typing import cast

from .config import load_provider_config
from .errors import ProviderConfigurationError, ProviderNotFoundError
from .models import (
    ChatRequest,
    ChatResponse,
    EmbeddingRequest,
    EmbeddingResponse,
)
from .provider import AIProvider
from .registry import ProviderRegistry


class ProviderManager:
    """Thread-safe provider selection and lifecycle manager."""

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()
        self.default_provider: str | None = None
        self._lock = RLock()

    def register(
        self,
        provider: AIProvider,
        *,
        default: bool = False,
        aliases: Iterable[str] = (),
    ) -> None:
        """Register and initialize one provider."""
        provider.validate_config()
        provider.initialize()
        with self._lock:
            self.registry.register(provider)
            self.registry.register_aliases(provider.name, aliases)
            if default or self.default_provider is None:
                self.default_provider = provider.name

    def register_alias(self, alias: str, provider: str) -> None:
        """Register an alternate name for an already registered provider."""
        with self._lock:
            self.registry.register_alias(alias, provider)

    @classmethod
    def from_config(
        cls, source: object, *, transports: dict[str, object] | None = None
    ) -> ProviderManager:
        """Build providers from YAML/JSON/dictionary configuration."""
        from .providers import (
            ClaudeProvider,
            DeepSeekProvider,
            GeminiProvider,
            OpenAICompatibleProvider,
            OpenAIProvider,
            OpenRouterProvider,
            QwenProvider,
        )

        default, configs = load_provider_config(source)  # type: ignore[arg-type]
        types = {
            "openai": OpenAIProvider,
            "openrouter": OpenRouterProvider,
            "deepseek": DeepSeekProvider,
            "qwen": QwenProvider,
            "anthropic": ClaudeProvider,
            "claude": ClaudeProvider,
            "gemini": GeminiProvider,
            "openai-compatible": OpenAICompatibleProvider,
        }
        manager = cls()
        for config in configs:
            provider_type = types.get(config.type)
            if provider_type is None:
                raise ValueError(f"Unknown provider type: {config.type}")
            transport = (transports or {}).get(config.name)
            provider = (
                provider_type(config=config, transport=transport)
                if config.type not in {"anthropic", "claude", "gemini"}
                else provider_type()
            )
            manager.register(provider, default=config.name == default)
        return manager

    load_config = from_config

    def initialize_all(self) -> None:
        """Initialize all registered providers idempotently."""
        for name in self.names():
            self.get(name).initialize()

    async def ainitialize_all(self) -> None:
        """Initialize all providers, awaiting async initializers when present."""
        for name in self.names():
            initializer = getattr(self.get(name), "ainitialize", None)
            if initializer is None:
                self.get(name).initialize()
                continue
            result = initializer()
            if inspect.isawaitable(result):
                await result

    def close_all(self) -> None:
        """Close all registered providers."""
        self.close()

    def unregister(self, name: str) -> AIProvider:
        """Close and unregister a provider."""
        with self._lock:
            provider = self.registry.unregister(name)
            provider.close()
            if self.default_provider == name:
                self.default_provider = None
            return provider

    def get(self, name: str | None = None) -> AIProvider:
        """Get the named or configured default provider."""
        selected = name or self.default_provider
        if selected is None:
            raise ProviderNotFoundError("No default provider is configured")
        try:
            return self.registry.get(selected)
        except Exception as exc:
            raise ProviderNotFoundError(
                f"Provider '{selected}' is not registered"
            ) from exc

    def names(self) -> list[str]:
        """Return stable registered provider names."""
        with self._lock:
            return self.registry.names()

    def aliases(self) -> dict[str, str]:
        """Return registered aliases and their canonical provider names."""
        with self._lock:
            return self.registry.aliases()

    def _route(
        self,
        request: ChatRequest,
        provider: str | None,
        model: str | None,
    ) -> tuple[AIProvider, ChatRequest]:
        """Resolve a provider and preserve a provider-prefixed model suffix."""
        selected = provider
        selected_model = model or request.model
        if selected is None and selected_model and "/" in selected_model:
            prefix, _, remainder = selected_model.partition("/")
            try:
                resolved = self.registry.resolve(prefix)
                self.registry.get(resolved)
            except ProviderNotFoundError:
                pass
            else:
                selected = resolved
                selected_model = remainder
        if selected_model != request.model:
            request = replace(request, model=selected_model)
        return self.get(selected), request

    def chat(
        self,
        request: ChatRequest,
        *,
        provider: str | None = None,
        model: str | None = None,
    ) -> ChatResponse:
        """Route a chat request."""
        selected_provider, selected_request = self._route(request, provider, model)
        return selected_provider.chat(selected_request)

    async def achat(
        self,
        request: ChatRequest,
        *,
        provider: str | None = None,
        model: str | None = None,
    ) -> ChatResponse:
        """Route chat through a provider's async API when it is available."""
        selected_provider, selected_request = self._route(request, provider, model)
        method = getattr(selected_provider, "achat", None)
        if method is None:
            return await asyncio.to_thread(selected_provider.chat, selected_request)
        response = method(selected_request)
        if not inspect.isawaitable(response):
            raise ProviderConfigurationError(
                f"Provider '{selected_provider.name}' returned a "
                "non-awaitable achat result"
            )
        return await cast(Awaitable[ChatResponse], response)

    def stream_chat(
        self,
        request: ChatRequest,
        *,
        provider: str | None = None,
        model: str | None = None,
    ) -> Iterator[ChatResponse]:
        """Route a synchronous chat stream without exposing provider internals."""
        selected_provider, selected_request = self._route(request, provider, model)
        return selected_provider.stream_chat(selected_request)

    async def astream_chat(
        self,
        request: ChatRequest,
        *,
        provider: str | None = None,
        model: str | None = None,
    ) -> AsyncIterator[ChatResponse]:
        """Route an asynchronous stream through the selected provider."""
        selected_provider, selected_request = self._route(request, provider, model)
        async for response in selected_provider.astream_chat(selected_request):
            yield response

    def health(self) -> dict[str, bool]:
        """Return provider health without mutating registrations."""
        return {name: self.get(name).health_check() for name in self.names()}

    def capabilities(self) -> dict[str, object]:
        """Return advertised capabilities by provider."""
        return {
            name: getattr(self.get(name), "capabilities", None) for name in self.names()
        }

    def embed(
        self, request: EmbeddingRequest, *, provider: str | None = None
    ) -> EmbeddingResponse:
        """Route an embedding request."""
        return self.get(provider).embed(request)

    def close(self) -> None:
        """Close all providers once."""
        for name in self.names():
            self.unregister(name)

    async def aclose(self) -> None:
        """Close and unregister providers, awaiting async close methods when present."""
        for name in self.names():
            with self._lock:
                provider = self.registry.unregister(name)
                if self.default_provider == name:
                    self.default_provider = None
            closer = getattr(provider, "aclose", None)
            if closer is None:
                await asyncio.to_thread(provider.close)
                continue
            result = closer()
            if inspect.isawaitable(result):
                await result
            else:
                await asyncio.to_thread(provider.close)
