"""Immutable, JSON-safe package catalog models without artifact behavior."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from ..models import MarketplaceValue, PackageDependency, PackageVersion


def _snapshot(value: Mapping[str, MarketplaceValue]) -> Mapping[str, MarketplaceValue]:
    """Return a defensive read-only metadata mapping."""
    return MappingProxyType(dict(value))


class PackageCategory(str, Enum):
    """Catalog categories; they do not select or run a package."""

    PROVIDER = "provider"
    WORKFLOW = "workflow"
    TOOL = "tool"
    PLUGIN = "plugin"
    MEMORY = "memory"
    TEMPLATE = "template"
    EXTENSION = "extension"


class PackageSort(str, Enum):
    """Deterministic catalog sort fields for local search results."""

    NAME = "name"
    PUBLISHER = "publisher"
    VERSION = "version"


@dataclass(frozen=True, slots=True)
class PackageTag:
    """A normalized descriptive tag with no remote taxonomy lookup."""

    value: str

    def __post_init__(self) -> None:
        if not self.value or self.value != self.value.strip():
            raise ValueError("Package tag must not be empty or padded.")


@dataclass(frozen=True, slots=True)
class PackageIconDescriptor:
    """An icon declaration only; it never fetches or decodes a remote resource."""

    name: str
    media_type: str = "image/svg+xml"

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Package icon requires a name.")


@dataclass(frozen=True, slots=True)
class PackageMetadata:
    """Descriptive package metadata with immutable extension values."""

    summary: str = ""
    icon: PackageIconDescriptor | None = None
    values: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _snapshot(self.values))


@dataclass(frozen=True, slots=True)
class PackageCompatibility:
    """Version declarations for Platform layers; no compatibility check is run."""

    runtime: str | None = None
    sdk: str | None = None
    studio: str | None = None
    enterprise: str | None = None
    cloud: str | None = None


CompatibilityDescriptor = PackageCompatibility


@dataclass(frozen=True, slots=True)
class PackageManifest:
    """Complete declarative manifest without an artifact, signature, or installer."""

    package_id: str
    publisher_id: str
    name: str
    description: str
    version: PackageVersion
    category: PackageCategory
    tags: frozenset[PackageTag] = field(default_factory=frozenset)
    compatibility: PackageCompatibility = field(default_factory=PackageCompatibility)
    dependencies: tuple[PackageDependency, ...] = ()
    metadata: PackageMetadata = field(default_factory=PackageMetadata)

    def __post_init__(self) -> None:
        if not all((self.package_id, self.publisher_id, self.name)):
            raise ValueError(
                "Package manifest id, publisher id, and name are required."
            )
        dependency_ids = tuple(
            dependency.package_id for dependency in self.dependencies
        )
        if len(set(dependency_ids)) != len(dependency_ids):
            raise ValueError(
                "Package manifest dependencies must not contain duplicates."
            )
        object.__setattr__(self, "tags", frozenset(self.tags))
        object.__setattr__(self, "dependencies", tuple(self.dependencies))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe manifest view with no executable package payload."""
        return {
            "package_id": self.package_id,
            "publisher_id": self.publisher_id,
            "name": self.name,
            "description": self.description,
            "version": str(self.version),
            "category": self.category.value,
            "tags": sorted(tag.value for tag in self.tags),
            "compatibility": {
                "runtime": self.compatibility.runtime,
                "sdk": self.compatibility.sdk,
                "studio": self.compatibility.studio,
                "enterprise": self.compatibility.enterprise,
                "cloud": self.compatibility.cloud,
            },
            "dependencies": [dependency.package_id for dependency in self.dependencies],
            "metadata": {
                "summary": self.metadata.summary,
                "icon": None if self.metadata.icon is None else self.metadata.icon.name,
                "values": dict(self.metadata.values),
            },
        }


@dataclass(frozen=True, slots=True)
class PackageDescriptor:
    """Catalog entry that wraps one immutable manifest and no package artifact."""

    manifest: PackageManifest
    featured: bool = False

    @property
    def package_id(self) -> str:
        """Expose the stable manifest package identifier."""
        return self.manifest.package_id

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe catalog descriptor."""
        return {"manifest": self.manifest.to_dict(), "featured": self.featured}


@dataclass(frozen=True, slots=True)
class PackageFilter:
    """Optional local catalog filters, all evaluated in memory."""

    category: PackageCategory | None = None
    publisher_id: str | None = None
    tag: PackageTag | None = None
    version: PackageVersion | None = None


@dataclass(frozen=True, slots=True)
class PackageQuery:
    """Immutable local search declaration with deterministic sort settings."""

    keyword: str | None = None
    package_filter: PackageFilter = field(default_factory=PackageFilter)
    sort: PackageSort = PackageSort.NAME
    descending: bool = False


@dataclass(frozen=True, slots=True)
class PackageSearchResult:
    """Immutable local search result with a stable total count."""

    packages: tuple[PackageDescriptor, ...]
    total: int

    def __post_init__(self) -> None:
        if self.total < 0:
            raise ValueError("Package search result total must not be negative.")
        object.__setattr__(self, "packages", tuple(self.packages))
