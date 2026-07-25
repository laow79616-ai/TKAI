"""Reference-only adapters for explicit Publication Foundation integration."""

from __future__ import annotations

from ..publication import PublicationSnapshot, PublicationStatus
from ..publisher import Publisher
from .errors import RegistryPublicationError
from .models import (
    RegistryCoordinate,
    RegistryEntry,
    RegistryEntryId,
    RegistryMetadata,
)


class ReferenceRegistryPublicationAdapter:
    """Convert accepted snapshots using an explicitly injected publisher descriptor."""

    def __init__(self, publisher: Publisher) -> None:
        self._publisher = publisher

    def entry_from_snapshot(
        self,
        entry_id: RegistryEntryId,
        snapshot: PublicationSnapshot,
        metadata: RegistryMetadata | None = None,
    ) -> RegistryEntry:
        """Adapt one accepted snapshot without querying a publication service."""
        if snapshot.status is not PublicationStatus.ACCEPTED:
            raise RegistryPublicationError(
                "Only accepted publication snapshots can be registered."
            )
        request = snapshot.request
        manifest = request.package_manifest
        if request.publisher_id != self._publisher.publisher_id:
            raise RegistryPublicationError(
                "Publication snapshot publisher does not match the injected publisher."
            )
        return RegistryEntry(
            entry_id=entry_id,
            coordinate=RegistryCoordinate(
                publisher_id=self._publisher.publisher_id,
                package_id=manifest.package_id,
                version=manifest.version,
            ),
            publication_id=str(snapshot.publication_id),
            package_manifest=manifest,
            publisher=self._publisher,
            category=manifest.category,
            dependencies=manifest.dependencies,
            compatibility=manifest.compatibility,
            tags=manifest.tags,
            metadata=metadata or RegistryMetadata(),
        )
