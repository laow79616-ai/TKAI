"""Catalog facade over an explicit Marketplace registry without network lookup."""

from __future__ import annotations

from .models import PackageDescriptor, PackageKind
from .registry import MarketplaceRegistry


class MarketplaceCatalog:
    """Read-only catalog projection of caller-owned registry state."""

    def __init__(self, registry: MarketplaceRegistry) -> None:
        self._registry = registry

    def packages(
        self, kind: PackageKind | None = None
    ) -> tuple[PackageDescriptor, ...]:
        """List descriptors in stable package-id order."""
        return self._registry.list(kind)

    def package(self, package_id: str) -> PackageDescriptor:
        """Resolve one local descriptor without remote catalog access."""
        return self._registry.get(package_id)
