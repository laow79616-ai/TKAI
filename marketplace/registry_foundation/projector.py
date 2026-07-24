"""Read-only projection from Registry Foundation entries to Catalog descriptors."""

from __future__ import annotations

from ..package_catalog import PackageDescriptor
from .models import RegistryEntry


class ReferenceRegistryCatalogProjector:
    """Project entries without holding or mutating a Marketplace Catalog service."""

    def project(self, entry: RegistryEntry) -> PackageDescriptor:
        """Return a new catalog descriptor derived from the entry manifest."""
        return PackageDescriptor(manifest=entry.package_manifest)
