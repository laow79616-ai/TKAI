"""Immutable publication descriptors with explicit data and no artifact handling."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from ..models import MarketplaceValue, PackageVersion
from ..package_catalog import PackageCategory, PackageCompatibility, PackageManifest
from ..publisher import Publisher, PublisherTier


def _snapshot(value: Mapping[str, MarketplaceValue]) -> Mapping[str, MarketplaceValue]:
    """Return a defensive immutable mapping without reading an external source."""
    return MappingProxyType(dict(value))


class PublicationStatus(str, Enum):
    """Reference publication lifecycle states; no remote workflow is invoked."""

    DRAFT = "draft"
    SUBMITTED = "submitted"
    VALIDATING = "validating"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class PublicationDecision(str, Enum):
    """Local validator decisions that do not grant publish permissions."""

    ACCEPT = "accept"
    REJECT = "reject"
    DEFER = "defer"


@dataclass(frozen=True, slots=True)
class PublicationId:
    """Explicit immutable publication identifier without automatic generation."""

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Publication id must not be empty.")

    def __str__(self) -> str:
        """Return the stable identifier text."""
        return self.value


@dataclass(frozen=True, slots=True)
class PublicationMetadata:
    """Publication-only metadata, independent of package catalog metadata."""

    values: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "values", _snapshot(self.values))


@dataclass(frozen=True, slots=True)
class PublicationManifest:
    """Explicit Publisher/PackageManifest boundary for one publication proposal."""

    publisher: Publisher
    package_manifest: PackageManifest
    metadata: PublicationMetadata = field(default_factory=PublicationMetadata)

    @property
    def publisher_id(self) -> str:
        """Expose the publisher identifier used for local publication coordinates."""
        return self.publisher.publisher_id

    @property
    def package_id(self) -> str:
        """Expose the package identifier without copying catalog state."""
        return self.package_manifest.package_id

    @property
    def version(self) -> PackageVersion:
        """Expose the manifest's explicit package version."""
        return self.package_manifest.version

    @property
    def category(self) -> PackageCategory:
        """Expose the manifest's explicit catalog category."""
        return self.package_manifest.category

    @property
    def compatibility(self) -> PackageCompatibility:
        """Expose the catalog compatibility declaration without evaluating it."""
        return self.package_manifest.compatibility

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe publication manifest view."""
        return {
            "publisher_id": self.publisher_id,
            "publisher_tier": self.publisher.tier.value,
            "package_manifest": self.package_manifest.to_dict(),
            "metadata": dict(self.metadata.values),
        }


@dataclass(frozen=True, slots=True)
class PublicationRequest:
    """Caller-owned publication request with no hidden time, account, or I/O state."""

    publication_id: PublicationId
    publisher_id: str
    package_manifest: PackageManifest
    requested_status: PublicationStatus = PublicationStatus.DRAFT
    metadata: PublicationMetadata = field(default_factory=PublicationMetadata)

    def __post_init__(self) -> None:
        if not self.publisher_id:
            raise ValueError("Publication request publisher id must not be empty.")
        if self.publisher_id != self.package_manifest.publisher_id:
            raise ValueError(
                "Publication request publisher id must match package manifest."
            )


@dataclass(frozen=True, slots=True)
class PublicationIssue:
    """Deterministic local validation issue with no environment detail."""

    code: str
    message: str
    field: str = ""


@dataclass(frozen=True, slots=True)
class PublicationResult:
    """Immutable validator result for one explicit publication request."""

    publication_id: PublicationId
    status: PublicationStatus
    decision: PublicationDecision
    issues: tuple[PublicationIssue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "issues", tuple(self.issues))

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe stable result view."""
        return {
            "publication_id": str(self.publication_id),
            "status": self.status.value,
            "decision": self.decision.value,
            "issues": [
                {"code": issue.code, "message": issue.message, "field": issue.field}
                for issue in self.issues
            ],
        }


@dataclass(frozen=True, slots=True)
class PublicationSnapshot:
    """Stable immutable service snapshot; it represents no remote publication."""

    request: PublicationRequest
    status: PublicationStatus
    result: PublicationResult | None = None

    @property
    def publication_id(self) -> PublicationId:
        """Expose the explicit snapshot identifier."""
        return self.request.publication_id

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe snapshot without credentials or artifacts."""
        return {
            "publication_id": str(self.publication_id),
            "publisher_id": self.request.publisher_id,
            "package_id": self.request.package_manifest.package_id,
            "version": str(self.request.package_manifest.version),
            "status": self.status.value,
            "result": None if self.result is None else self.result.to_dict(),
            "metadata": dict(self.request.metadata.values),
        }


@dataclass(frozen=True, slots=True)
class PublicationPolicyRule:
    """Descriptive local policy rule; it has no authorization semantics."""

    name: str
    enabled: bool = True
    description: str = ""


@dataclass(frozen=True, slots=True)
class PublicationPolicy:
    """Declarative local rules for structural publication validation only."""

    allow_community_submission: bool = True
    required_publisher_tier: PublisherTier | None = None
    allow_prerelease: bool = True
    allow_empty_dependencies: bool = True
    allow_unknown_compatibility_targets: bool = True
    allow_duplicate_coordinate: bool = False
    max_tag_count: int = 16
    max_metadata_entries: int = 32
    rules: tuple[PublicationPolicyRule, ...] = ()

    def __post_init__(self) -> None:
        if self.max_tag_count < 0 or self.max_metadata_entries < 0:
            raise ValueError("Publication policy limits must not be negative.")
        object.__setattr__(self, "rules", tuple(self.rules))


@dataclass(frozen=True, slots=True)
class PublicationPolicyResult:
    """Pure policy evaluation result with stably ordered local issues."""

    decision: PublicationDecision
    issues: tuple[PublicationIssue, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "issues", tuple(self.issues))
