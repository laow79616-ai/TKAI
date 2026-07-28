"""Enterprise App Store domain values."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    SUSPENDED = "suspended"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Visibility(str, Enum):
    PRIVATE = "private"
    WORKSPACE = "workspace"
    ORGANIZATION = "organization"
    TENANT = "tenant"
    PUBLIC = "public"


class LicenseKind(str, Enum):
    OPEN_SOURCE = "open_source"
    COMMERCIAL = "commercial"
    TRIAL = "trial"
    SUBSCRIPTION = "subscription"
    ENTERPRISE = "enterprise"
    OFFLINE = "offline"


class ReleaseChannel(str, Enum):
    STABLE = "stable"
    BETA = "beta"
    PRIVATE = "private"


class InstallationStatus(str, Enum):
    INSTALLED = "installed"
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNINSTALLED = "uninstalled"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class Scope:
    tenant: str
    organization: str
    workspace: str

    def __post_init__(self) -> None:
        if not self.tenant or not self.organization or not self.workspace:
            raise ValueError("Tenant, organization, and workspace are required.")


@dataclass(frozen=True, slots=True)
class Compatibility:
    platform: str = "tkai"
    minimum_version: str = "3.1"
    maximum_version: str | None = None
    architectures: tuple[str, ...] = ("amd64", "arm64")


@dataclass(frozen=True, slots=True)
class Pricing:
    model: str = "free"
    currency: str = "USD"
    amount: float = 0
    billing_period: str | None = None


@dataclass(frozen=True, slots=True)
class StoreApplication:
    id: str
    name: str
    description: str
    version: str
    publisher: str
    category: str
    tenant: str
    organization: str
    workspace: str
    tags: tuple[str, ...] = ()
    icon_reference: str | None = None
    screenshots: tuple[str, ...] = ()
    status: ApplicationStatus = ApplicationStatus.DRAFT
    visibility: Visibility = Visibility.PRIVATE
    compatibility: Compatibility = field(default_factory=Compatibility)
    license: LicenseKind = LicenseKind.OPEN_SOURCE
    pricing: Pricing = field(default_factory=Pricing)
    metadata: dict[str, Any] = field(default_factory=dict)
    featured: bool = False
    verified: bool = False

    @property
    def scope(self) -> Scope:
        return Scope(self.tenant, self.organization, self.workspace)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Publisher:
    id: str
    name: str
    organization: str
    owner: str
    tenant: str
    workspace: str
    verified: bool = False
    signing_identity: str | None = None
    support_contact: str | None = None
    release_history: tuple[str, ...] = ()

    @property
    def scope(self) -> Scope:
        return Scope(self.tenant, self.organization, self.workspace)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Package:
    id: str
    application_id: str
    version: str
    manifest: dict[str, Any]
    dependencies: tuple[str, ...]
    compatibility: Compatibility
    checksum: str
    signature: str
    artifact_reference: str
    installation_instructions: tuple[str, ...] = ()
    upgrade_instructions: tuple[str, ...] = ()
    rollback_instructions: tuple[str, ...] = ()
    size_bytes: int = 0
    channel: ReleaseChannel = ReleaseChannel.STABLE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Installation:
    id: str
    application_id: str
    package_id: str
    version: str
    scope: Scope
    status: InstallationStatus
    permissions: tuple[str, ...] = ()
    pinned_version: str | None = None
    automatic_updates: bool = False
    release_channel: ReleaseChannel = ReleaseChannel.STABLE

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class License:
    id: str
    application_id: str
    scope: Scope
    kind: LicenseKind
    active: bool = False
    seat_limit: int | None = None
    tenant_limit: int | None = None
    expires_at: str | None = None
    offline: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Subscription:
    id: str
    application_id: str
    scope: Scope
    plan: str
    entitlements: tuple[str, ...] = ()
    quota: int | None = None
    usage: int = 0
    renews_at: str | None = None
    cancelled: bool = False
    invoice_reference: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class Review:
    id: str
    application_id: str
    scope: Scope
    actor: str
    rating: int
    comment: str
    verified_installation: bool
    moderated: bool = False
    abuse_reports: int = 0
    publisher_reply: str | None = None

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 5:
            raise ValueError("Rating must be between one and five.")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
