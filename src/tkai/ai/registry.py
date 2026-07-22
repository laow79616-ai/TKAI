"""Registry for unified AI providers."""

from __future__ import annotations

from tkai.core.exceptions import AIProviderError

from .provider import AIProvider


class ProviderRegistry:
    """Register and retrieve providers by their stable service name."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}

    def register(self, provider: AIProvider, *, overwrite: bool = False) -> None:
        """Register a provider, rejecting accidental duplicates."""
        if provider.name in self._providers and not overwrite:
            raise AIProviderError(f"Provider '{provider.name}' already registered")
        self._providers[provider.name] = provider

    def get(self, name: str) -> AIProvider:
        """Return a provider by name."""
        try:
            return self._providers[name]
        except KeyError as exc:
            raise AIProviderError(f"Provider '{name}' is not registered") from exc

    def names(self) -> list[str]:
        """Return names in stable order."""
        return sorted(self._providers)
