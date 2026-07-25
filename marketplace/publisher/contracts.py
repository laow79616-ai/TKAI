"""Publisher verification and trust extension contracts with no remote calls."""

from __future__ import annotations

from typing import Protocol

from .models import Publisher, PublisherTier


class PublisherVerification(Protocol):
    """Future verification boundary; no identity or evidence check is implemented."""

    def verify(self, publisher: Publisher) -> bool: ...


class PublisherTrust(Protocol):
    """Future trust boundary; no reputation or policy lookup is implemented."""

    def tier_for(self, publisher: Publisher) -> PublisherTier: ...
