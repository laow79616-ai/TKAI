"""Extensible local credential-provider protocol."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable

from .models import Credential


class CredentialProvider(ABC):
    """A local source of credentials; implementations must not perform network I/O."""

    @abstractmethod
    def load(self, provider: str) -> Credential | None:
        """Load one credential or return ``None`` when it is unavailable."""

    @abstractmethod
    def supports(self, provider: str) -> bool:
        """Return whether this source can resolve the provider name."""

    @abstractmethod
    def identifier(self) -> str:
        """Return a stable non-secret source identifier."""

    def providers(self) -> Iterable[str]:
        """Return discoverable provider names when the source can enumerate them."""
        return ()
