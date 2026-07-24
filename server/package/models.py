"""Immutable, deterministic Marketplace Server Package domain models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def _copy(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(values))


class PackageCategory(str, Enum):
    """Descriptive Package categories without installation semantics."""

    PROVIDER = "provider"
    WORKFLOW = "workflow"
    TOOL = "tool"
    PLUGIN = "plugin"
    MEMORY = "memory"
    TEMPLATE = "template"
    EXTENSION = "extension"


class PackageStatus(str, Enum):
    """Descriptive Package lifecycle states."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    WITHDRAWN = "withdrawn"
    DELETED = "deleted"


class PackageEventType(str, Enum):
    """Deterministic Package events with no time or EventBus dependency."""

    CREATED = "created"
    UPDATED = "updated"
    DEPRECATED = "deprecated"
    WITHDRAWN = "withdrawn"
    DELETED = "deleted"
    RESTORED = "restored"
    CLOSED = "closed"


class PackageSort(str, Enum):
    """Stable local Package sorting keys."""

    PACKAGE_ID = "package_id"
    PUBLISHER = "publisher"
    CATEGORY = "category"
    VERSION = "version"


@dataclass(frozen=True, slots=True)
class PackageId:
    """Explicit Package identifier without Registry lookup semantics."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Package id must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PackageTag:
    """Descriptive Package tag without a remote catalog index."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Package tag must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PackageVersionRef:
    """Declared Package version reference; no artifact is resolved or downloaded."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Package version must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PackageMetadata:
    """Defensively copied descriptive metadata with no credentials or paths."""

    values: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _copy(self.values))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready defensive metadata copy."""
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class PackageDescriptor:
    """Local Package description independent of Publisher and Registry services."""

    publisher: str
    name: str
    category: PackageCategory
    description: str = ""
    tags: frozenset[PackageTag] = field(default_factory=frozenset)
    metadata: PackageMetadata = field(default_factory=PackageMetadata)

    def __post_init__(self) -> None:
        if not self.publisher or not self.name:
            raise ValueError("Package publisher and name are required.")
        object.__setattr__(self, "tags", frozenset(self.tags))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-ready Package descriptor."""
        return {
            "publisher": self.publisher,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "tags": sorted(str(tag) for tag in self.tags),
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class PackageManifest:
    """Package descriptor with an explicit version reference and no artifact data."""

    descriptor: PackageDescriptor
    version: PackageVersionRef
    metadata: PackageMetadata = field(default_factory=PackageMetadata)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready manifest representation."""
        return {
            "descriptor": self.descriptor.to_dict(),
            "version": str(self.version),
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class PackageRecord:
    """Immutable Package manifest plus a descriptive local lifecycle state."""

    package_id: PackageId
    manifest: PackageManifest
    status: PackageStatus = PackageStatus.ACTIVE

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Package record."""
        return {
            "package_id": str(self.package_id),
            "manifest": self.manifest.to_dict(),
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class PackageEvent:
    """Sequence-ordered local Package event without timestamps."""

    sequence: int
    event_type: PackageEventType
    package_id: PackageId | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Package event."""
        return {
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "package_id": None if self.package_id is None else str(self.package_id),
        }


@dataclass(frozen=True, slots=True)
class PackageStatistics:
    """Count-only Package statistics calculated from current local records."""

    packages: int = 0
    active: int = 0
    deprecated: int = 0
    withdrawn: int = 0
    deleted: int = 0
    categories: int = 0
    versions: int = 0
    tags: int = 0

    def to_dict(self) -> dict[str, int]:
        """Return JSON-ready count-only Package statistics."""
        return {
            "packages": self.packages,
            "active": self.active,
            "deprecated": self.deprecated,
            "withdrawn": self.withdrawn,
            "deleted": self.deleted,
            "categories": self.categories,
            "versions": self.versions,
            "tags": self.tags,
        }


@dataclass(frozen=True, slots=True)
class PackageFilter:
    """Explicit local Package search filters."""

    publisher: str | None = None
    category: PackageCategory | None = None
    tag: str | None = None
    version: str | None = None
    status: PackageStatus | None = None


@dataclass(frozen=True, slots=True)
class PackageQuery:
    """Deterministic local Package query; empty queries list all Package records."""

    keyword: str = ""
    package_filter: PackageFilter = field(default_factory=PackageFilter)
    sort: PackageSort = PackageSort.PACKAGE_ID
    descending: bool = False


@dataclass(frozen=True, slots=True)
class PackageSearchResult:
    """Immutable, stable locally filtered Package search results."""

    packages: tuple[PackageRecord, ...] = ()
    total: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "packages", tuple(self.packages))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Package search result."""
        return {
            "packages": [package.to_dict() for package in self.packages],
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class PackageSnapshot:
    """Stable immutable local Package records, events, statistics, and close state."""

    packages: tuple[PackageRecord, ...] = ()
    events: tuple[PackageEvent, ...] = ()
    statistics: PackageStatistics = field(default_factory=PackageStatistics)
    closed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "packages", tuple(self.packages))
        object.__setattr__(self, "events", tuple(self.events))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready immutable Package snapshot."""
        return {
            "packages": [package.to_dict() for package in self.packages],
            "events": [event.to_dict() for event in self.events],
            "statistics": self.statistics.to_dict(),
            "closed": self.closed,
        }
