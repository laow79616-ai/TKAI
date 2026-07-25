"""Explicit factory for offline immutable Publisher descriptors."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from ..models import MarketplaceValue
from .models import (
    Publisher,
    PublisherCapability,
    PublisherOrganization,
    PublisherProfile,
    PublisherTier,
)


class PublisherFactory:
    """Create Publisher descriptors from explicit caller-provided declarations."""

    def create(
        self,
        publisher_id: str,
        display_name: str,
        *,
        description: str = "",
        website: str | None = None,
        tier: PublisherTier = PublisherTier.COMMUNITY,
        organization: PublisherOrganization | None = None,
        capabilities: Iterable[PublisherCapability] = (),
        metadata: Mapping[str, MarketplaceValue] | None = None,
    ) -> Publisher:
        """Build an immutable publisher without account discovery or network access."""
        return Publisher(
            publisher_id,
            PublisherProfile(
                display_name,
                description,
                website,
                {} if metadata is None else metadata,
            ),
            tier,
            organization,
            frozenset(capabilities),
            {} if metadata is None else metadata,
        )
