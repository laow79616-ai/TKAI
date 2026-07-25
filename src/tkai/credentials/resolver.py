"""Deterministic priority-based local credential resolution."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import CredentialNotFoundError
from .models import Credential
from .provider import CredentialProvider


class CredentialResolver:
    """Resolve credentials from ordered local sources without validating them."""

    def __init__(self, providers: Iterable[CredentialProvider]) -> None:
        self._providers = tuple(providers)

    def resolve(self, provider: str) -> Credential:
        """Return the first non-empty credential according to configured priority."""
        for source in self._providers:
            if source.supports(provider):
                credential = source.load(provider)
                if credential is not None:
                    return credential
        raise CredentialNotFoundError(
            f"No credential is configured for provider '{provider}'"
        )

    def has(self, provider: str) -> bool:
        """Return whether resolution succeeds without exposing values."""
        try:
            self.resolve(provider)
        except CredentialNotFoundError:
            return False
        return True

    def providers(self) -> list[str]:
        """Return stable discoverable provider names from all local sources."""
        return sorted(
            {name for source in self._providers for name in source.providers()}
        )

    def sources_for(self, provider: str) -> list[str]:
        """Return all sources currently containing a credential for diagnostics."""
        return [
            source.identifier()
            for source in self._providers
            if source.supports(provider) and source.load(provider) is not None
        ]

    def reload(self) -> None:
        """Reload sources that expose a local reload hook."""
        for source in self._providers:
            reload_method = getattr(source, "reload", None)
            if callable(reload_method):
                reload_method()
