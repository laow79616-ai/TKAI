"""Immutable Marketplace descriptors with no artifact or network behavior."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

MarketplaceValue = str | int | float | bool | None


def _snapshot(value: Mapping[str, MarketplaceValue]) -> Mapping[str, MarketplaceValue]:
    """Return a read-only defensive metadata snapshot."""
    return MappingProxyType(dict(value))


class PackageKind(str, Enum):
    """Supported Marketplace package declarations, not executable components."""

    PLUGIN = "plugin"
    PROVIDER = "provider"
    MEMORY = "memory"
    WORKFLOW = "workflow"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class PackageVersion:
    """Small explicit semantic-version descriptor without a resolver dependency."""

    major: int
    minor: int = 0
    patch: int = 0
    prerelease: str | None = None

    def __post_init__(self) -> None:
        if min(self.major, self.minor, self.patch) < 0:
            raise ValueError("Package version components must not be negative.")
        if self.prerelease is not None and not self.prerelease:
            raise ValueError("Package prerelease must not be empty when provided.")

    def __str__(self) -> str:
        """Render the stable version text used by package descriptors."""
        base = f"{self.major}.{self.minor}.{self.patch}"
        return base if self.prerelease is None else f"{base}-{self.prerelease}"


@dataclass(frozen=True, slots=True)
class PackageDependency:
    """A declarative dependency; it neither downloads nor installs anything."""

    package_id: str
    version_constraint: str | None = None
    required: bool = True

    def __post_init__(self) -> None:
        if not self.package_id:
            raise ValueError("Package dependency requires a package id.")


@dataclass(frozen=True, slots=True)
class PublisherDescriptor:
    """Publisher identity declaration without accounts or remote verification."""

    publisher_id: str
    name: str
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.publisher_id or not self.name:
            raise ValueError("Publisher id and name are required.")
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class PackageDescriptor:
    """A catalog entry for a reference package, never an artifact payload."""

    package_id: str
    name: str
    kind: PackageKind
    version: PackageVersion
    publisher: PublisherDescriptor
    description: str = ""
    dependencies: tuple[PackageDependency, ...] = ()
    capabilities: frozenset[str] = field(default_factory=frozenset)
    signature: str | None = None
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.package_id or not self.name:
            raise ValueError("Package id and name are required.")
        identifiers = tuple(dependency.package_id for dependency in self.dependencies)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("Package dependencies must not contain duplicates.")
        object.__setattr__(self, "dependencies", tuple(self.dependencies))
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "metadata", _snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe catalog view without package payloads or credentials."""
        return {
            "package_id": self.package_id,
            "name": self.name,
            "kind": self.kind.value,
            "version": str(self.version),
            "publisher": self.publisher.publisher_id,
            "description": self.description,
            "dependencies": [dependency.package_id for dependency in self.dependencies],
            "capabilities": sorted(self.capabilities),
            "signature": self.signature,
            "metadata": dict(self.metadata),
        }
