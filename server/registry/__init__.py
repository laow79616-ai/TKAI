"""Reference-only Marketplace Server Registry Foundation exports."""

from .errors import (
    RegistryClosedError,
    RegistryConflictError,
    RegistryError,
    RegistryNotFoundError,
    RegistryStateError,
    RegistryValidationError,
)
from .models import (
    RegistryCoordinate,
    RegistryDescriptor,
    RegistryEntry,
    RegistryEvent,
    RegistryEventType,
    RegistryFilter,
    RegistryId,
    RegistryMetadata,
    RegistryQuery,
    RegistrySearchResult,
    RegistrySnapshot,
    RegistrySort,
    RegistryStatistics,
    RegistryStatus,
)
from .service import ReferenceRegistryService
from .storage import ReferenceRegistryStorage, RegistryStorage

__all__ = (
    "ReferenceRegistryService",
    "ReferenceRegistryStorage",
    "RegistryClosedError",
    "RegistryConflictError",
    "RegistryCoordinate",
    "RegistryDescriptor",
    "RegistryEntry",
    "RegistryError",
    "RegistryEvent",
    "RegistryEventType",
    "RegistryFilter",
    "RegistryId",
    "RegistryMetadata",
    "RegistryNotFoundError",
    "RegistryQuery",
    "RegistrySearchResult",
    "RegistrySnapshot",
    "RegistrySort",
    "RegistryStateError",
    "RegistryStatistics",
    "RegistryStatus",
    "RegistryStorage",
    "RegistryValidationError",
)
