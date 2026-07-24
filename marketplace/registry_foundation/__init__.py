"""Reference-only Registry Foundation, separate from legacy Marketplace APIs."""

from .adapter import ReferenceRegistryPublicationAdapter
from .contracts import RegistryCatalogProjector, RegistryPublicationAdapter
from .errors import (
    RegistryClosedError,
    RegistryConflictError,
    RegistryError,
    RegistryNotFoundError,
    RegistryPublicationError,
    RegistryStateError,
    RegistryValidationError,
)
from .models import (
    RegistryCoordinate,
    RegistryEntry,
    RegistryEntryId,
    RegistryEvent,
    RegistryEventType,
    RegistryFilter,
    RegistryIndex,
    RegistryMetadata,
    RegistryQuery,
    RegistrySearchResult,
    RegistrySnapshot,
    RegistrySort,
    RegistryStatistics,
    RegistryStatus,
)
from .projector import ReferenceRegistryCatalogProjector
from .service import ReferenceRegistryService

__all__ = [
    "ReferenceRegistryCatalogProjector",
    "ReferenceRegistryPublicationAdapter",
    "ReferenceRegistryService",
    "RegistryCatalogProjector",
    "RegistryClosedError",
    "RegistryConflictError",
    "RegistryCoordinate",
    "RegistryEntry",
    "RegistryEntryId",
    "RegistryError",
    "RegistryEvent",
    "RegistryEventType",
    "RegistryFilter",
    "RegistryIndex",
    "RegistryMetadata",
    "RegistryNotFoundError",
    "RegistryPublicationAdapter",
    "RegistryPublicationError",
    "RegistryQuery",
    "RegistrySearchResult",
    "RegistrySnapshot",
    "RegistrySort",
    "RegistryStateError",
    "RegistryStatistics",
    "RegistryStatus",
    "RegistryValidationError",
]
