"""Registry for unified AI providers."""

from __future__ import annotations

from collections.abc import Iterable

from tkai.core.exceptions import AIProviderError

from .errors import ProviderNotFoundError
from .provider import AIProvider


class ProviderRegistry:
    """Register and retrieve providers by their stable service name."""

    def __init__(self) -> None:
        self._providers: dict[str, AIProvider] = {}
        self._aliases: dict[str, str] = {}

    def register(self, provider: AIProvider, *, overwrite: bool = False) -> None:
        """Register a provider, rejecting accidental duplicates."""
        if provider.name in self._providers and not overwrite:
            raise AIProviderError(f"Provider '{provider.name}' already registered")
        self._providers[provider.name] = provider

    def register_alias(self, alias: str, provider_name: str) -> None:
        """Bind ``alias`` to a registered provider name.

        Aliases are deliberately resolved by the registry so every manager
        operation uses the same provider collection and routing rules.
        """
        if not alias:
            raise AIProviderError("Provider alias cannot be empty")
        if alias in self._providers:
            raise AIProviderError(f"Provider alias '{alias}' conflicts with a provider")
        if alias in self._aliases:
            raise AIProviderError(f"Provider alias '{alias}' already registered")
        if provider_name not in self._providers:
            raise ProviderNotFoundError(f"Provider '{provider_name}' is not registered")
        self._aliases[alias] = provider_name

    def register_aliases(self, provider_name: str, aliases: Iterable[str]) -> None:
        """Bind each alias to ``provider_name`` atomically where possible."""
        aliases = tuple(aliases)
        if provider_name not in self._providers:
            raise ProviderNotFoundError(f"Provider '{provider_name}' is not registered")
        for alias in aliases:
            if not alias or alias in self._providers or alias in self._aliases:
                raise AIProviderError(f"Provider alias '{alias}' is unavailable")
        for alias in aliases:
            self._aliases[alias] = provider_name

    def get(self, name: str) -> AIProvider:
        """Return a provider by name."""
        try:
            return self._providers[self.resolve(name)]
        except KeyError as exc:
            raise ProviderNotFoundError(f"Provider '{name}' is not registered") from exc

    def resolve(self, name: str) -> str:
        """Return the canonical provider name for a name or alias."""
        return self._aliases.get(name, name)

    def unregister(self, name: str) -> AIProvider:
        """Remove and return a provider."""
        try:
            canonical_name = self.resolve(name)
            provider = self._providers.pop(canonical_name)
        except KeyError as exc:
            raise ProviderNotFoundError(f"Provider '{name}' is not registered") from exc
        self._aliases = {
            alias: target
            for alias, target in self._aliases.items()
            if target != canonical_name
        }
        return provider

    def names(self) -> list[str]:
        """Return names in stable order."""
        return sorted(self._providers)

    def aliases(self) -> dict[str, str]:
        """Return aliases and their canonical provider names in stable order."""
        return {name: self._aliases[name] for name in sorted(self._aliases)}
