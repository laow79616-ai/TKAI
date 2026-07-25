"""Immutable and deterministic Marketplace Server Publisher descriptors."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def _copy(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(values))


class PublisherLevel(str, Enum):
    """Descriptive Publisher levels that do not grant permissions."""

    COMMUNITY = "community"
    VERIFIED = "verified"
    OFFICIAL = "official"
    ENTERPRISE = "enterprise"


class PublisherStatus(str, Enum):
    """Descriptive Publisher lifecycle states."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    DELETED = "deleted"


class PublisherEventType(str, Enum):
    """Deterministic events recorded by the reference Publisher service."""

    CREATED = "created"
    UPDATED = "updated"
    SUSPENDED = "suspended"
    RESTORED = "restored"
    DEPRECATED = "deprecated"
    DELETED = "deleted"
    CAPABILITY_ADDED = "capability_added"
    CAPABILITY_REMOVED = "capability_removed"
    CLEARED = "cleared"
    CLOSED = "closed"


class PublisherSort(str, Enum):
    """Stable local sorting keys for Publisher searches."""

    PUBLISHER_ID = "publisher_id"
    NAME = "name"
    LEVEL = "level"
    STATUS = "status"


@dataclass(frozen=True, slots=True)
class PublisherId:
    """Explicit Publisher identifier without account lookup semantics."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Publisher id must not be empty.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class PublisherMetadata:
    """Defensively copied descriptive metadata with no credentials."""

    values: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _copy(self.values))

    def to_dict(self) -> dict[str, object]:
        """Return a defensive JSON-ready metadata copy."""
        return dict(self.values)


@dataclass(frozen=True, slots=True)
class PublisherCapability:
    """A declarative capability that neither authorizes nor enforces behavior."""

    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Publisher capability requires a name.")

    def to_dict(self) -> dict[str, str]:
        """Return a JSON-ready capability representation."""
        return {"name": self.name, "description": self.description}


@dataclass(frozen=True, slots=True)
class PublisherOrganization:
    """Optional organization descriptor without an Enterprise directory lookup."""

    organization_id: str
    name: str
    metadata: PublisherMetadata = field(default_factory=PublisherMetadata)

    def __post_init__(self) -> None:
        if not self.organization_id or not self.name:
            raise ValueError("Publisher organization id and name are required.")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready organization representation."""
        return {
            "organization_id": self.organization_id,
            "name": self.name,
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class PublisherProfile:
    """Presentation data without a remote Publisher account or login."""

    name: str
    description: str = ""
    metadata: PublisherMetadata = field(default_factory=PublisherMetadata)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Publisher profile name is required.")

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready profile representation."""
        return {
            "name": self.name,
            "description": self.description,
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class PublisherDescriptor:
    """Complete declarative Publisher description for local reference storage."""

    profile: PublisherProfile
    level: PublisherLevel = PublisherLevel.COMMUNITY
    organization: PublisherOrganization | None = None
    capabilities: frozenset[PublisherCapability] = field(default_factory=frozenset)
    metadata: PublisherMetadata = field(default_factory=PublisherMetadata)

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-ready Publisher description."""
        return {
            "profile": self.profile.to_dict(),
            "level": self.level.value,
            "organization": (
                None if self.organization is None else self.organization.to_dict()
            ),
            "capabilities": [
                capability.to_dict()
                for capability in sorted(self.capabilities, key=lambda item: item.name)
            ],
            "metadata": self.metadata.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class PublisherRecord:
    """Publisher descriptor plus an explicitly managed descriptive lifecycle state."""

    publisher_id: PublisherId
    descriptor: PublisherDescriptor
    status: PublisherStatus = PublisherStatus.ACTIVE

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready Publisher record."""
        return {
            "publisher_id": str(self.publisher_id),
            "descriptor": self.descriptor.to_dict(),
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class PublisherEvent:
    """Sequence-ordered local event with no timestamp or EventBus publication."""

    sequence: int
    event_type: PublisherEventType
    publisher_id: PublisherId | None = None

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready event representation."""
        return {
            "sequence": self.sequence,
            "event_type": self.event_type.value,
            "publisher_id": (
                None if self.publisher_id is None else str(self.publisher_id)
            ),
        }


@dataclass(frozen=True, slots=True)
class PublisherStatistics:
    """Fresh count-only statistics calculated from current local records."""

    total_publishers: int = 0
    active: int = 0
    suspended: int = 0
    deprecated: int = 0
    deleted: int = 0
    community: int = 0
    verified: int = 0
    official: int = 0
    enterprise: int = 0
    organizations: int = 0
    capabilities: int = 0

    def to_dict(self) -> dict[str, int]:
        """Return JSON-ready count-only statistics."""
        return {
            "total_publishers": self.total_publishers,
            "active": self.active,
            "suspended": self.suspended,
            "deprecated": self.deprecated,
            "deleted": self.deleted,
            "community": self.community,
            "verified": self.verified,
            "official": self.official,
            "enterprise": self.enterprise,
            "organizations": self.organizations,
            "capabilities": self.capabilities,
        }


@dataclass(frozen=True, slots=True)
class PublisherFilter:
    """Explicit local Publisher search filters."""

    publisher_id: str | None = None
    name: str | None = None
    organization: str | None = None
    level: PublisherLevel | None = None
    status: PublisherStatus | None = None
    capability: str | None = None


@dataclass(frozen=True, slots=True)
class PublisherQuery:
    """Deterministic local Publisher query; an empty query returns all records."""

    keyword: str = ""
    publisher_filter: PublisherFilter = field(default_factory=PublisherFilter)
    sort: PublisherSort = PublisherSort.PUBLISHER_ID
    descending: bool = False


@dataclass(frozen=True, slots=True)
class PublisherSearchResult:
    """Immutable locally filtered Publisher records in deterministic order."""

    publishers: tuple[PublisherRecord, ...] = ()
    total: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "publishers", tuple(self.publishers))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready search result."""
        return {
            "publishers": [publisher.to_dict() for publisher in self.publishers],
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class PublisherSnapshot:
    """Stable immutable Reference Publisher service state."""

    publishers: tuple[PublisherRecord, ...] = ()
    events: tuple[PublisherEvent, ...] = ()
    statistics: PublisherStatistics = field(default_factory=PublisherStatistics)
    closed: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "publishers", tuple(self.publishers))
        object.__setattr__(self, "events", tuple(self.events))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-ready immutable snapshot representation."""
        return {
            "publishers": [publisher.to_dict() for publisher in self.publishers],
            "events": [event.to_dict() for event in self.events],
            "statistics": self.statistics.to_dict(),
            "closed": self.closed,
        }
