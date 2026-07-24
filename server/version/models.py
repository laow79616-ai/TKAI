"""Immutable, deterministic Marketplace Server Version domain models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def _copy(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(values))


class VersionStatus(str, Enum):
    """Descriptive Version lifecycle states."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    WITHDRAWN = "withdrawn"
    DELETED = "deleted"


class VersionLabel(str, Enum):
    """Descriptive Version labels without release-pipeline behavior."""

    STABLE = "stable"
    PRERELEASE = "prerelease"
    BETA = "beta"
    ALPHA = "alpha"


class VersionEventType(str, Enum):
    """Deterministic Version events with no timestamp or EventBus dependency."""

    CREATED = "created"
    UPDATED = "updated"
    DEPRECATED = "deprecated"
    WITHDRAWN = "withdrawn"
    DELETED = "deleted"
    RESTORED = "restored"
    CLOSED = "closed"


class VersionSort(str, Enum):
    """Stable local Version sorting keys."""

    VERSION_ID = "version_id"
    PACKAGE = "package"
    PUBLISHER = "publisher"
    SEMANTIC_VERSION = "semantic_version"


@dataclass(frozen=True, slots=True)
class VersionId:
    """Explicit Version identifier with no Package service lookup semantics."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Version id must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class VersionMetadata:
    """Defensively copied descriptive metadata without paths or credentials."""

    values: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _copy(self.values))

    def to_dict(self) -> dict[str, object]:
        """Return a defensive JSON-ready metadata copy."""
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class VersionDescriptor:
    """Version description with explicit string Package and Publisher references."""

    package: str
    publisher: str
    semantic_version: str
    label: VersionLabel = VersionLabel.STABLE
    description: str = ""
    metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def __post_init__(self) -> None:
        if not self.package or not self.publisher or not self.semantic_version:
            raise ValueError(
                "Version package, publisher, and semantic version are required."
            )

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Version descriptor."""
        return {
            "package": self.package,
            "publisher": self.publisher,
            "semantic_version": self.semantic_version,
            "label": self.label.value,
            "description": self.description,
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class VersionManifest:
    """Explicit Version declaration with no artifact, signature, or release pipeline."""

    descriptor: VersionDescriptor
    metadata: VersionMetadata = field(default_factory=VersionMetadata)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Version manifest."""
        return {
            "descriptor": self.descriptor.to_dict(),
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class VersionRecord:
    """Immutable Version manifest plus a descriptive local lifecycle state."""

    version_id: VersionId
    manifest: VersionManifest
    status: VersionStatus = VersionStatus.ACTIVE

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Version record."""
        return {
            "version_id": str(self.version_id),
            "manifest": self.manifest.to_dict(),
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class VersionEvent:
    """Sequence-ordered local Version event without timestamps."""

    sequence: int
    event_type: VersionEventType
    version_id: VersionId | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Version event."""
        return {
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "version_id": None if self.version_id is None else str(self.version_id),
        }


@dataclass(frozen=True, slots=True)
class VersionStatistics:
    """Count-only statistics calculated from current local Version records."""

    versions: int = 0
    active: int = 0
    deprecated: int = 0
    withdrawn: int = 0
    deleted: int = 0
    stable: int = 0
    prerelease: int = 0
    beta: int = 0
    alpha: int = 0

    def to_dict(self) -> dict[str, int]:
        """Return JSON-ready count-only Version statistics."""
        return {
            "versions": self.versions,
            "active": self.active,
            "deprecated": self.deprecated,
            "withdrawn": self.withdrawn,
            "deleted": self.deleted,
            "stable": self.stable,
            "prerelease": self.prerelease,
            "beta": self.beta,
            "alpha": self.alpha,
        }


@dataclass(frozen=True, slots=True)
class VersionFilter:
    """Explicit local Version search filters."""

    package: str | None = None
    publisher: str | None = None
    semantic_version: str | None = None
    status: VersionStatus | None = None
    label: VersionLabel | None = None


@dataclass(frozen=True, slots=True)
class VersionQuery:
    """Deterministic local Version query; empty queries list all records."""

    keyword: str = ""
    version_filter: VersionFilter = field(default_factory=VersionFilter)
    sort: VersionSort = VersionSort.VERSION_ID
    descending: bool = False


@dataclass(frozen=True, slots=True)
class VersionSearchResult:
    """Immutable locally filtered Version results in stable order."""

    versions: tuple[VersionRecord, ...] = ()
    total: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "versions", tuple(self.versions))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Version search result."""
        return {
            "versions": [version.to_dict() for version in self.versions],
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class VersionSnapshot:
    """Stable immutable Version records, events, statistics, and close state."""

    versions: tuple[VersionRecord, ...] = ()
    events: tuple[VersionEvent, ...] = ()
    statistics: VersionStatistics = field(default_factory=VersionStatistics)
    closed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "versions", tuple(self.versions))
        object.__setattr__(self, "events", tuple(self.events))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready immutable Version snapshot."""
        return {
            "versions": [version.to_dict() for version in self.versions],
            "events": [event.to_dict() for event in self.events],
            "statistics": self.statistics.to_dict(),
            "closed": self.closed,
        }
