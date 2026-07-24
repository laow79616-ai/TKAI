"""Thread-safe explicit registry for injected Identity providers."""

from __future__ import annotations

from threading import RLock

from .errors import IdentityConflictError, IdentityNotFoundError
from .providers import IdentityProvider


class IdentityRegistry:
    """Registers injected providers without creating a default identity provider."""

    def __init__(self) -> None:
        self._providers: dict[str, IdentityProvider] = {}
        self._lock = RLock()

    def register(self, provider: IdentityProvider) -> None:
        """Register one provider by its descriptor identifier."""
        provider_id = provider.descriptor.provider_id
        with self._lock:
            if provider_id in self._providers:
                raise IdentityConflictError(
                    f"Identity provider {provider_id!r} is already registered."
                )
            self._providers[provider_id] = provider

    def unregister(self, provider_id: str) -> IdentityProvider:
        """Remove and return an explicitly registered provider."""
        with self._lock:
            try:
                return self._providers.pop(provider_id)
            except KeyError as exc:
                raise IdentityNotFoundError(
                    f"Identity provider {provider_id!r} was not found."
                ) from exc

    def lookup(self, provider_id: str) -> IdentityProvider:
        """Find one provider without changing registry state."""
        with self._lock:
            try:
                return self._providers[provider_id]
            except KeyError as exc:
                raise IdentityNotFoundError(
                    f"Identity provider {provider_id!r} was not found."
                ) from exc

    def list(self) -> tuple[IdentityProvider, ...]:
        """Return providers in deterministic identifier order."""
        with self._lock:
            return tuple(self._providers[key] for key in sorted(self._providers))

    def supports(self, capability: str) -> tuple[IdentityProvider, ...]:
        """Return explicitly declared capability matches in stable order."""
        return tuple(
            provider
            for provider in self.list()
            if capability in provider.capabilities()
        )
