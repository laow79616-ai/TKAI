"""Immutable license descriptors; they never enforce features or read license files."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from types import MappingProxyType

LicenseValue = str | int | float | bool | None


def _snapshot(value: Mapping[str, LicenseValue]) -> Mapping[str, LicenseValue]:
    return MappingProxyType(dict(value))


class Edition(str, Enum):
    COMMUNITY = "community"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True, slots=True)
class LicenseCapability:
    name: str
    enabled: bool = True


@dataclass(frozen=True, slots=True)
class FeatureDescriptor:
    name: str
    description: str = ""
    metadata: Mapping[str, LicenseValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class FeatureGroup:
    name: str
    features: tuple[FeatureDescriptor, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "features", tuple(self.features))


@dataclass(frozen=True, slots=True)
class CapabilitySnapshot:
    edition: Edition
    capabilities: tuple[LicenseCapability, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "capabilities", tuple(self.capabilities))


@dataclass(frozen=True, slots=True)
class LicenseGrant:
    feature: str
    granted: bool = True


@dataclass(frozen=True, slots=True)
class LicenseLimit:
    name: str
    limit: int | None


@dataclass(frozen=True, slots=True)
class LicenseUsage:
    name: str
    used: int


@dataclass(frozen=True, slots=True)
class Expiration:
    expires_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class GracePeriod:
    days: int = 0


@dataclass(frozen=True, slots=True)
class RenewalHint:
    message: str = ""


@dataclass(frozen=True, slots=True)
class LicenseEntitlement:
    entitlement_id: str
    edition: Edition
    grants: tuple[LicenseGrant, ...] = ()
    limits: tuple[LicenseLimit, ...] = ()
    expiration: Expiration = field(default_factory=Expiration)
    grace_period: GracePeriod = field(default_factory=GracePeriod)
    renewal_hint: RenewalHint = field(default_factory=RenewalHint)
    metadata: Mapping[str, LicenseValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "grants", tuple(self.grants))
        object.__setattr__(self, "limits", tuple(self.limits))
        object.__setattr__(self, "metadata", _snapshot(self.metadata))
