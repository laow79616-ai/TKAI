"""Immutable local Registry Foundation models with no storage or time source."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from ..models import MarketplaceValue, PackageDependency, PackageVersion
from ..package_catalog import (
    PackageCategory,
    PackageCompatibility,
    PackageManifest,
    PackageTag,
)
from ..publisher import Publisher


def _snapshot(value: Mapping[str, MarketplaceValue]) -> Mapping[str, MarketplaceValue]:
    """Return a defensive read-only metadata mapping."""
    return MappingProxyType(dict(value))


class RegistryStatus(str, Enum):
    """Descriptive entry status with no package deletion or client notification."""

    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    DEPRECATED = "deprecated"


class RegistryEventType(str, Enum):
    """In-memory descriptive service events; they do not reach an EventBus."""

    REGISTERED = "registered"
    UNREGISTERED = "unregistered"
    WITHDRAWN = "withdrawn"
    RESTORED = "restored"
    DEPRECATED = "deprecated"
    CLEARED = "cleared"
    CLOSED = "closed"


class RegistrySort(str, Enum):
    """Deterministic local Registry Foundation sort fields."""

    PACKAGE_ID = "package_id"
    PUBLISHER_ID = "publisher_id"
    VERSION = "version"
    CATEGORY = "category"
    STATUS = "status"


@dataclass(frozen=True, slots=True)
class RegistryEntryId:
    """Explicit local registry entry identifier; no id generation occurs."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Registry entry id must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RegistryCoordinate:
    """Unique local package coordinate used for deterministic duplicate checks."""

    publisher_id: str
    package_id: str
    version: PackageVersion

    def __post_init__(self) -> None:
        if not self.publisher_id or not self.package_id:
            raise ValueError(
                "Registry coordinate publisher and package ids are required."
            )

    def key(self) -> tuple[str, str, str]:
        return (self.publisher_id, self.package_id, str(self.version))


@dataclass(frozen=True, slots=True)
class RegistryMetadata:
    """Registry-only metadata that never includes package artifact contents."""

    values: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _snapshot(self.values))


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """Immutable entry derived explicitly from an accepted publication only."""

    entry_id: RegistryEntryId
    coordinate: RegistryCoordinate
    publication_id: str
    package_manifest: PackageManifest
    publisher: Publisher
    category: PackageCategory
    dependencies: tuple[PackageDependency, ...]
    compatibility: PackageCompatibility
    tags: frozenset[PackageTag]
    status: RegistryStatus = RegistryStatus.ACTIVE
    metadata: RegistryMetadata = field(default_factory=RegistryMetadata)

    def __post_init__(self) -> None:
        if not self.publication_id:
            raise ValueError("Registry entry requires a publication id.")
        if self.coordinate.publisher_id != self.publisher.publisher_id:
            raise ValueError(
                "Registry coordinate publisher must match entry publisher."
            )
        if self.coordinate.package_id != self.package_manifest.package_id:
            raise ValueError("Registry coordinate package must match entry manifest.")
        if self.coordinate.version != self.package_manifest.version:
            raise ValueError("Registry coordinate version must match entry manifest.")
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        object.__setattr__(self, "tags", frozenset(self.tags))

    def to_dict(self) -> dict[str, object]:
        return {
            "entry_id": str(self.entry_id),
            "coordinate": {
                "publisher_id": self.coordinate.publisher_id,
                "package_id": self.coordinate.package_id,
                "version": str(self.coordinate.version),
            },
            "publication_id": self.publication_id,
            "category": self.category.value,
            "status": self.status.value,
            "tags": sorted(tag.value for tag in self.tags),
            "metadata": dict(self.metadata.values),
        }


@dataclass(frozen=True, slots=True)
class RegistryIndex:
    """Immutable descriptive index view; no mutable index map is exposed."""

    coordinates: Mapping[tuple[str, str, str], str] = field(default_factory=dict)
    package_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    publisher_ids: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    categories: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    versions: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    tags: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    statuses: Mapping[str, tuple[str, ...]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in (
            "coordinates",
            "package_ids",
            "publisher_ids",
            "categories",
            "versions",
            "tags",
            "statuses",
        ):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


@dataclass(frozen=True, slots=True)
class RegistrySnapshot:
    """Stable immutable Registry Foundation snapshot in entry-id order."""

    entries: tuple[RegistryEntry, ...]
    index: RegistryIndex

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))


@dataclass(frozen=True, slots=True)
class RegistryStatistics:
    """Current descriptive counts calculated from a local immutable snapshot."""

    total_entries: int
    active_entries: int
    withdrawn_entries: int
    deprecated_entries: int
    publishers: int
    packages: int
    versions: int
    categories: int


@dataclass(frozen=True, slots=True)
class RegistryEvent:
    """Stable sequence-ordered local registry event without a system timestamp."""

    sequence: int
    event_type: RegistryEventType
    entry_id: RegistryEntryId | None = None
    coordinate: RegistryCoordinate | None = None
    metadata: RegistryMetadata = field(default_factory=RegistryMetadata)


@dataclass(frozen=True, slots=True)
class RegistryFilter:
    publisher_id: str | None = None
    package_id: str | None = None
    category: PackageCategory | None = None
    version: PackageVersion | None = None
    tag: PackageTag | None = None
    status: RegistryStatus | None = None


@dataclass(frozen=True, slots=True)
class RegistryQuery:
    keyword: str | None = None
    registry_filter: RegistryFilter = field(default_factory=RegistryFilter)
    sort: RegistrySort = RegistrySort.PACKAGE_ID
    descending: bool = False


@dataclass(frozen=True, slots=True)
class RegistrySearchResult:
    entries: tuple[RegistryEntry, ...]
    total: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "entries", tuple(self.entries))
