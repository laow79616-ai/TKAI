"""Immutable Publisher Foundation descriptors without account or network logic."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from ..models import MarketplaceValue


def _snapshot(value: Mapping[str, MarketplaceValue]) -> Mapping[str, MarketplaceValue]:
    """Return a defensive immutable metadata view."""
    return MappingProxyType(dict(value))


class PublisherTier(str, Enum):
    """Descriptive trust tiers; they do not grant privileges or enforce policy."""

    COMMUNITY = "community"
    VERIFIED = "verified"
    OFFICIAL = "official"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True, slots=True)
class PublisherCapability:
    """A declarative publisher capability without execution semantics."""

    name: str
    description: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Publisher capability requires a name.")


@dataclass(frozen=True, slots=True)
class PublisherOrganization:
    """Optional organization association with no Enterprise-directory lookup."""

    organization_id: str
    name: str
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.organization_id or not self.name:
            raise ValueError("Publisher organization id and name are required.")
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class PublisherProfile:
    """Publisher presentation data; it has no login, account, or profile API."""

    display_name: str
    description: str = ""
    website: str | None = None
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.display_name:
            raise ValueError("Publisher profile requires a display name.")
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class Publisher:
    """Offline publisher descriptor with explicit caller-supplied relationships."""

    publisher_id: str
    profile: PublisherProfile
    tier: PublisherTier = PublisherTier.COMMUNITY
    organization: PublisherOrganization | None = None
    capabilities: frozenset[PublisherCapability] = field(default_factory=frozenset)
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.publisher_id:
            raise ValueError("Publisher requires an id.")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "metadata", _snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe descriptor without accounts, secrets, or package data."""
        return {
            "publisher_id": self.publisher_id,
            "display_name": self.profile.display_name,
            "tier": self.tier.value,
            "organization_id": (
                None if self.organization is None else self.organization.organization_id
            ),
            "capabilities": sorted(capability.name for capability in self.capabilities),
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class PublisherValidation:
    """Policy result that describes validity without taking action."""

    valid: bool
    warnings: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()
