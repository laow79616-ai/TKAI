"""Offline reference Publisher service with explicit local collaborators."""

from __future__ import annotations

from .factory import PublisherFactory
from .models import Publisher, PublisherTier
from .registry import PublisherRegistry


class ReferencePublisherService:
    """Compose a local registry and factory without verification or network I/O."""

    def __init__(
        self,
        registry: PublisherRegistry | None = None,
        factory: PublisherFactory | None = None,
    ) -> None:
        self._registry = registry if registry is not None else PublisherRegistry()
        self._factory = factory if factory is not None else PublisherFactory()

    @property
    def registry(self) -> PublisherRegistry:
        """Expose the explicit local registry for caller-owned lifecycle control."""
        return self._registry

    def create(
        self,
        publisher_id: str,
        display_name: str,
        *,
        tier: PublisherTier = PublisherTier.COMMUNITY,
    ) -> Publisher:
        """Create and register one reference publisher from explicit values only."""
        return self._registry.register(
            self._factory.create(publisher_id, display_name, tier=tier)
        )

    def publisher(self, publisher_id: str) -> Publisher:
        """Return one local immutable publisher descriptor."""
        return self._registry.get(publisher_id)

    def publishers(self, tier: PublisherTier | None = None) -> tuple[Publisher, ...]:
        """Return local publisher descriptors in stable order."""
        return self._registry.list(tier)

    def close(self) -> None:
        """Idempotently release local in-memory reference state."""
        self._registry.clear()
