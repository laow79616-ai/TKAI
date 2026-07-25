"""Declarative Publisher policy validation without trust enforcement."""

from __future__ import annotations

from .models import Publisher, PublisherTier, PublisherValidation


class PublisherPolicy:
    """Describe Publisher declaration validity without registration side effects."""

    def validate_creation(self, publisher: Publisher) -> PublisherValidation:
        """Return warnings for descriptive tiers that lack a declared organization."""
        warnings: list[str] = []
        if (
            publisher.tier in {PublisherTier.OFFICIAL, PublisherTier.ENTERPRISE}
            and publisher.organization is None
        ):
            warnings.append("Official or Enterprise publisher has no organization.")
        return PublisherValidation(True, tuple(warnings))
