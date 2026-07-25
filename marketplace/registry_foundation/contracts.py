"""Explicit adapters that keep Registry Foundation independent of other services."""

from __future__ import annotations

from typing import Protocol

from ..package_catalog import PackageDescriptor
from ..publication import PublicationSnapshot
from .models import RegistryEntry, RegistryEntryId, RegistryMetadata


class RegistryPublicationAdapter(Protocol):
    """Adapt one caller-provided accepted publication snapshot into an entry."""

    def entry_from_snapshot(
        self,
        entry_id: RegistryEntryId,
        snapshot: PublicationSnapshot,
        metadata: RegistryMetadata | None = None,
    ) -> RegistryEntry:
        """Return an immutable entry or raise a registry publication error."""


class RegistryCatalogProjector(Protocol):
    """Create a catalog descriptor without writing to any catalog service."""

    def project(self, entry: RegistryEntry) -> PackageDescriptor:
        """Project the supplied immutable entry into a catalog descriptor."""
