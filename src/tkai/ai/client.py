"""High-level facade for provider-neutral AI generation."""

from __future__ import annotations

from typing import Any

from .models import AIResponse
from .provider import AIProvider
from .registry import ProviderRegistry


class AIClient:
    """Route requests to providers registered under a unified interface."""

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()

    def register(self, provider: AIProvider, *, overwrite: bool = False) -> None:
        """Register one provider for later request routing."""
        self.registry.register(provider, overwrite=overwrite)

    def generate(
        self, provider: str, prompt: str, *, model: str | None = None, **options: Any
    ) -> AIResponse:
        """Generate text using the named provider."""
        return self.registry.get(provider).generate(prompt, model=model, **options)
