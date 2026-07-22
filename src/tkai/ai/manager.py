"""Lifecycle and routing facade for registered AI providers."""

from __future__ import annotations

from threading import RLock

from .config import load_provider_config
from .errors import ProviderNotFoundError
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

    def register(self, provider: AIProvider, *, default: bool = False) -> None:
        """Register and initialize one provider."""
        provider.validate_config()
        provider.initialize()
        with self._lock:
            self.registry.register(provider)
            if default or self.default_provider is None:
                self.default_provider = provider.name

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

    def chat(
        self, request: ChatRequest, *, provider: str | None = None
    ) -> ChatResponse:
        """Route a chat request."""
        return self.get(provider).chat(request)

    def embed(
        self, request: EmbeddingRequest, *, provider: str | None = None
    ) -> EmbeddingResponse:
        """Route an embedding request."""
        return self.get(provider).embed(request)

    def close(self) -> None:
        """Close all providers once."""
        for name in self.names():
            self.unregister(name)
