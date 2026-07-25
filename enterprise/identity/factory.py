"""Explicit factory for offline reference Identity providers."""

from __future__ import annotations

from collections.abc import Mapping

from .models import IdentityDescriptor, IdentityPrincipal
from .providers import ReferenceIdentityProvider


class IdentityFactory:
    """Creates only explicitly requested reference/test identity components."""

    @staticmethod
    def reference_provider(
        descriptor: IdentityDescriptor,
        principals: Mapping[str, IdentityPrincipal] | None = None,
    ) -> ReferenceIdentityProvider:
        """Create a deterministic provider with no network or environment access."""
        return ReferenceIdentityProvider(descriptor, principals)
