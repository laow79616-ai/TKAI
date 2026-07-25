"""Read-only credential management facade."""

from __future__ import annotations

from .models import Credential
from .resolver import CredentialResolver


class CredentialManager:
    """Expose resolution, safe listing, masking, and reload without network checks."""

    def __init__(self, resolver: CredentialResolver) -> None:
        self.resolver = resolver

    def get(self, provider: str) -> Credential:
        """Return a resolved immutable credential."""
        return self.resolver.resolve(provider)

    def has(self, provider: str) -> bool:
        """Return whether any source resolves the provider."""
        return self.resolver.has(provider)

    def list(self) -> list[Credential]:
        """Return resolved credentials for discoverable providers in stable order."""
        return [
            self.get(provider)
            for provider in self.resolver.providers()
            if self.has(provider)
        ]

    def mask(self, provider: str) -> str:
        """Return the credential's safe redacted representation."""
        return self.get(provider).masked()

    def reload(self) -> None:
        """Refresh local source snapshots without validating any API key."""
        self.resolver.reload()
