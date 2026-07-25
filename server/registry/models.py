"""Immutable, deterministic descriptors for the Server Registry Foundation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def _copy(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


class RegistryStatus(str, Enum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    WITHDRAWN = "withdrawn"
    DELETED = "deleted"


class RegistryEventType(str, Enum):
    CREATED = "created"
    UPDATED = "updated"
    DEPRECATED = "deprecated"
    WITHDRAWN = "withdrawn"
    DELETED = "deleted"
    RESTORED = "restored"
    SNAPSHOT = "snapshot"
    CLOSED = "closed"


class RegistrySort(str, Enum):
    ENTRY_ID = "entry_id"
    PUBLISHER = "publisher"
    PACKAGE = "package"
    VERSION = "version"


@dataclass(frozen=True, slots=True)
class RegistryId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Registry id must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RegistryCoordinate:
    publisher: str
    package: str
    version: str

    def __post_init__(self) -> None:
        if not self.publisher or not self.package or not self.version:
            raise ValueError("Registry publisher, package, and version are required.")

    def key(self) -> tuple[str, str, str]:
        return (self.publisher, self.package, self.version)

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-ready representation of this coordinate."""
        return {
            "publisher": self.publisher,
            "package": self.package,
            "version": self.version,
        }


@dataclass(frozen=True, slots=True)
class RegistryMetadata:
    values: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _copy(self.values))

    def to_dict(self) -> dict[str, object]:
        """Return a defensive JSON-ready metadata copy."""
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class RegistryDescriptor:
    coordinate: RegistryCoordinate
    title: str = ""
    metadata: RegistryMetadata = field(default_factory=RegistryMetadata)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready descriptor representation."""
        return {
            "coordinate": self.coordinate.to_dict(),
            "title": self.title,
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    registry_id: RegistryId
    descriptor: RegistryDescriptor
    status: RegistryStatus = RegistryStatus.ACTIVE

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready entry representation."""
        return {
            "registry_id": str(self.registry_id),
            "descriptor": self.descriptor.to_dict(),
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class RegistryEvent:
    sequence: int
    event_type: RegistryEventType
    registry_id: RegistryId | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready event representation."""
        return {
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "registry_id": None if self.registry_id is None else str(self.registry_id),
        }


@dataclass(frozen=True, slots=True)
class RegistryStatistics:
    entries: int = 0
    active: int = 0
    deprecated: int = 0
    withdrawn: int = 0
    deleted: int = 0
    publishers: int = 0
    packages: int = 0
    versions: int = 0

    def to_dict(self) -> dict[str, int]:
        """Return count-only statistics suitable for JSON serialization."""
        return {
            "entries": self.entries,
            "active": self.active,
            "deprecated": self.deprecated,
            "withdrawn": self.withdrawn,
            "deleted": self.deleted,
            "publishers": self.publishers,
            "packages": self.packages,
            "versions": self.versions,
        }


@dataclass(frozen=True, slots=True)
class RegistryFilter:
    publisher: str | None = None
    package: str | None = None
    version: str | None = None
    status: RegistryStatus | None = None


@dataclass(frozen=True, slots=True)
class RegistryQuery:
    keyword: str = ""
    registry_filter: RegistryFilter = field(default_factory=RegistryFilter)
    sort: RegistrySort = RegistrySort.ENTRY_ID
    descending: bool = False


@dataclass(frozen=True, slots=True)
class RegistrySearchResult:
    entries: tuple[RegistryEntry, ...] = ()
    total: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready, stable search result."""
        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    entries: tuple[RegistryEntry, ...] = ()
    events: tuple[RegistryEvent, ...] = ()
    statistics: RegistryStatistics = field(default_factory=RegistryStatistics)
    closed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
        object.__setattr__(self, "events", tuple(self.events))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready immutable snapshot representation."""
        return {
            "entries": [entry.to_dict() for entry in self.entries],
            "events": [event.to_dict() for event in self.events],
            "statistics": self.statistics.to_dict(),
            "closed": self.closed,
        }
