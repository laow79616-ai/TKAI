"""Read-only adaptation of Registry Foundation snapshots for local resolution."""

from __future__ import annotations

from typing import Protocol

from ..registry_foundation import RegistryEntry, RegistrySnapshot
from .models import DependencyCoordinate


class RegistryResolutionSource(Protocol):
    """Expose stable, local candidate entries without a Registry service dependency."""

    def candidates(self) -> tuple[RegistryEntry, ...]:
        """Return a defensive stable candidate collection."""


class ReferenceRegistryResolutionSource:
    """Capture one explicit RegistrySnapshot without retaining its service instance."""

    def __init__(self, snapshot: RegistrySnapshot) -> None:
        self._candidates = tuple(
            sorted(snapshot.entries, key=lambda entry: self.coordinate_for(entry).key())
        )

    def candidates(self) -> tuple[RegistryEntry, ...]:
        """Return the immutable captured candidate tuple."""
        return tuple(self._candidates)

    @staticmethod
    def coordinate_for(entry: RegistryEntry) -> DependencyCoordinate:
        """Convert an immutable Registry entry coordinate into resolver terminology."""
        return DependencyCoordinate(
            entry.coordinate.publisher_id,
            entry.coordinate.package_id,
            entry.coordinate.version,
        )
