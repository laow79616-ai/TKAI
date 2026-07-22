"""Runtime-injected local credential source."""

from __future__ import annotations

from collections.abc import Mapping

from ..models import Credential
from .static import StaticCredentialProvider


class RuntimeCredentialProvider(StaticCredentialProvider):
    """Mutable in-process source intended for application runtime injection."""

    def __init__(self, credentials: Mapping[str, Credential] | None = None) -> None:
        super().__init__(credentials or {}, identifier="runtime")

    def set(self, credential: Credential) -> None:
        """Inject a credential for this process without persisting it."""
        self._credentials[credential.provider.lower()] = credential

    def remove(self, provider: str) -> None:
        """Remove an injected credential from this process."""
        self._credentials.pop(provider.lower(), None)
