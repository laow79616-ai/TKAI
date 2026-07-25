"""Static/test credential source."""

from __future__ import annotations

from collections.abc import Mapping

from ..models import Credential
from ..provider import CredentialProvider


class StaticCredentialProvider(CredentialProvider):
    """Resolve explicitly supplied immutable credentials for tests or embedding."""

    def __init__(
        self, credentials: Mapping[str, Credential], identifier: str = "static"
    ) -> None:
        self._credentials = dict(credentials)
        self._identifier = identifier

    def load(self, provider: str) -> Credential | None:
        """Return a copy with this source's identifier."""
        credential = self._credentials.get(provider.lower())
        if credential is None:
            return None
        return Credential(
            provider=credential.provider,
            api_key=credential.api_key,
            organization=credential.organization,
            base_url=credential.base_url,
            extra_headers=credential.extra_headers,
            source=self.identifier(),
        )

    def supports(self, provider: str) -> bool:
        """Return whether an explicit credential exists for the provider."""
        return provider.lower() in self._credentials

    def identifier(self) -> str:
        """Return the configured non-secret source name."""
        return self._identifier

    def providers(self) -> list[str]:
        """Return stable explicit provider names."""
        return sorted(self._credentials)
