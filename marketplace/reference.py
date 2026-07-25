"""Offline reference Marketplace composed from explicit local collaborators."""

from __future__ import annotations

from .catalog import MarketplaceCatalog
from .dependency import DependencyGraph
from .models import PackageDescriptor, PackageKind
from .registry import MarketplaceRegistry


class ReferenceMarketplace:
    """A local catalog composition with no hidden Platform or network access."""

    def __init__(self, registry: MarketplaceRegistry | None = None) -> None:
        self._registry = registry if registry is not None else MarketplaceRegistry()
        self._catalog = MarketplaceCatalog(self._registry)

    @property
    def registry(self) -> MarketplaceRegistry:
        """Expose the explicit caller-owned local registry."""
        return self._registry

    @property
    def catalog(self) -> MarketplaceCatalog:
        """Expose the read-only local catalog facade."""
        return self._catalog

    def publish(self, package: PackageDescriptor) -> PackageDescriptor:
        """Register a descriptor only; no artifact is uploaded or distributed."""
        return self._registry.register(package)

    def packages(
        self, kind: PackageKind | None = None
    ) -> tuple[PackageDescriptor, ...]:
        """List local descriptors without network catalog discovery."""
        return self._catalog.packages(kind)

    def dependency_graph(self) -> DependencyGraph:
        """Create a pure dependency view of the current immutable snapshot."""
        return DependencyGraph(self._registry.snapshot())

    def close(self) -> None:
        """Idempotently clear local reference declarations."""
        self._registry.clear()
