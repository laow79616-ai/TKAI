"""Enterprise Marketplace domain service.

The service is deliberately storage and transport neutral. It provides an
offline reference implementation that API, dashboard, and persistence adapters
can compose without coupling the Marketplace to the existing plugin runtime.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from hashlib import sha256
from hmac import compare_digest
from types import MappingProxyType


class StoreKind(str, Enum):
    """Enterprise store package types."""

    AGENT = "agent"
    PLUGIN = "plugin"
    WORKFLOW = "workflow"
    PROMPT = "prompt"
    DATASET = "dataset"
    KNOWLEDGE = "knowledge"
    MODEL = "model"
    TEMPLATE = "template"
    EXTENSION = "extension"


class LicenseKind(str, Enum):
    """Supported licensing plans."""

    COMMERCIAL = "commercial"
    ENTERPRISE = "enterprise"
    OPEN_SOURCE = "open-source"
    TRIAL = "trial"
    SUBSCRIPTION = "subscription"
    OFFLINE = "offline"


@dataclass(frozen=True, slots=True)
class PublisherProfile:
    """Verified organization and ownership identity."""

    publisher_id: str
    organization: str
    display_name: str
    verified: bool = False
    owners: tuple[str, ...] = ()
    signing_key_id: str | None = None


@dataclass(frozen=True, slots=True)
class MarketplacePackage:
    """One immutable package release."""

    package_id: str
    name: str
    kind: StoreKind
    publisher_id: str
    version: str
    category: str
    tags: frozenset[str] = field(default_factory=frozenset)
    dependencies: tuple[str, ...] = ()
    compatibility: frozenset[str] = field(default_factory=frozenset)
    checksum: str = ""
    signature: str = ""
    featured: bool = False
    verified: bool = False
    downloads: int = 0
    releases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-safe package representation."""
        return {
            "package_id": self.package_id,
            "name": self.name,
            "kind": self.kind.value,
            "publisher_id": self.publisher_id,
            "version": self.version,
            "category": self.category,
            "tags": sorted(self.tags),
            "dependencies": list(self.dependencies),
            "compatibility": sorted(self.compatibility),
            "checksum": self.checksum,
            "signature": self.signature,
            "featured": self.featured,
            "verified": self.verified,
            "downloads": self.downloads,
            "releases": list(self.releases),
        }


@dataclass(frozen=True, slots=True)
class MarketplaceLicense:
    """A commercial, enterprise, open, trial, subscription, or offline grant."""

    license_id: str
    package_id: str
    kind: LicenseKind
    seats: int | None = None
    offline: bool = False
    subscription_id: str | None = None
    active: bool = True


@dataclass(frozen=True, slots=True)
class Review:
    """A verified or unverified package review."""

    review_id: str
    package_id: str
    author: str
    rating: int
    comment: str = ""
    verified_purchase: bool = False
    moderated: bool = False

    def __post_init__(self) -> None:
        if not 1 <= self.rating <= 5:
            raise ValueError("Rating must be between 1 and 5.")


@dataclass(frozen=True, slots=True)
class Invoice:
    """Transport-neutral purchase invoice."""

    invoice_id: str
    account_id: str
    package_id: str
    amount: int
    currency: str = "USD"
    status: str = "open"


@dataclass(frozen=True, slots=True)
class Usage:
    """Package quota usage."""

    account_id: str
    package_id: str
    used: int
    quota: int


class MarketplaceMetrics:
    """Required count-only Marketplace metrics."""

    NAMES = (
        "packages_total",
        "downloads_total",
        "publishers_total",
        "licenses_total",
        "installs_total",
        "ratings_total",
    )

    def __init__(self) -> None:
        self._values: Counter[str] = Counter()

    def set(self, name: str, value: int) -> None:
        if name not in self.NAMES:
            raise ValueError(f"Unknown marketplace metric: {name}")
        self._values[name] = value

    def increment(self, name: str, amount: int = 1) -> None:
        if name not in self.NAMES:
            raise ValueError(f"Unknown marketplace metric: {name}")
        self._values[name] += amount

    def snapshot(self) -> Mapping[str, int]:
        return MappingProxyType({name: self._values[name] for name in self.NAMES})

    def render_prometheus(self) -> str:
        lines: list[str] = []
        for name, value in self.snapshot().items():
            metric = f"tkai_marketplace_{name}"
            lines.extend((f"# TYPE {metric} gauge", f"{metric} {value}"))
        return "\n".join(lines) + "\n"


class EnterpriseMarketplace:
    """In-memory enterprise store with deterministic lifecycle operations."""

    def __init__(self) -> None:
        self.publishers: dict[str, PublisherProfile] = {}
        self.packages: dict[str, dict[str, MarketplacePackage]] = {}
        self.installed: dict[str, str] = {}
        self.install_history: dict[str, list[str]] = {}
        self.licenses: dict[str, MarketplaceLicense] = {}
        self.reviews: dict[str, Review] = {}
        self.invoices: dict[str, Invoice] = {}
        self.usage: dict[tuple[str, str], Usage] = {}
        self.download_log: list[str] = []
        self.metrics = MarketplaceMetrics()

    def register_publisher(self, profile: PublisherProfile) -> PublisherProfile:
        if profile.publisher_id in self.publishers:
            raise ValueError(f"Publisher already exists: {profile.publisher_id}")
        self.publishers[profile.publisher_id] = profile
        self.metrics.set("publishers_total", len(self.publishers))
        return profile

    def verify_publisher(self, publisher_id: str) -> PublisherProfile:
        profile = self.publishers[publisher_id]
        verified = replace(profile, verified=True)
        self.publishers[publisher_id] = verified
        return verified

    def publish(self, package: MarketplacePackage) -> MarketplacePackage:
        publisher = self.publishers.get(package.publisher_id)
        if publisher is None:
            raise ValueError(f"Unknown publisher: {package.publisher_id}")
        versions = self.packages.setdefault(package.package_id, {})
        if package.version in versions:
            raise ValueError("Package version already exists.")
        releases = tuple((*self.release_history(package.package_id), package.version))
        stored = replace(package, verified=publisher.verified, releases=releases)
        versions[package.version] = stored
        self.metrics.set("packages_total", len(self.packages))
        return stored

    def search(
        self,
        query: str = "",
        *,
        category: str | None = None,
        tag: str | None = None,
        kind: StoreKind | None = None,
        featured: bool | None = None,
        verified: bool | None = None,
        trending: bool = False,
    ) -> tuple[MarketplacePackage, ...]:
        needle = query.casefold()
        result = [
            package
            for package in self.latest_packages()
            if (
                not needle
                or needle in package.name.casefold()
                or needle in package.package_id.casefold()
            )
            and (category is None or package.category == category)
            and (tag is None or tag in package.tags)
            and (kind is None or package.kind is kind)
            and (featured is None or package.featured is featured)
            and (verified is None or package.verified is verified)
        ]
        if trending:
            return tuple(
                sorted(result, key=lambda item: (-item.downloads, item.package_id))
            )
        return tuple(sorted(result, key=lambda item: (item.package_id, item.version)))

    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({item.category for item in self.latest_packages()}))

    def tags(self) -> tuple[str, ...]:
        return tuple(
            sorted({tag for item in self.latest_packages() for tag in item.tags})
        )

    def stores(self) -> Mapping[str, tuple[MarketplacePackage, ...]]:
        return MappingProxyType(
            {kind.value: self.search(kind=kind) for kind in StoreKind}
        )

    def install(
        self, package_id: str, version: str | None = None
    ) -> MarketplacePackage:
        package = self._version(package_id, version)
        self._validate_dependencies(package)
        previous = self.installed.get(package_id)
        if previous is not None:
            self.install_history.setdefault(package_id, []).append(previous)
        self.installed[package_id] = package.version
        self.metrics.increment("installs_total")
        return package

    def upgrade(
        self, package_id: str, version: str | None = None
    ) -> MarketplacePackage:
        if package_id not in self.installed:
            raise ValueError("Package is not installed.")
        return self.install(package_id, version)

    def rollback(self, package_id: str) -> MarketplacePackage:
        history = self.install_history.get(package_id, [])
        if not history:
            raise ValueError("No rollback release is available.")
        version = history.pop()
        self.installed[package_id] = version
        return self._version(package_id, version)

    def dependency_graph(self, package_id: str) -> tuple[str, ...]:
        ordered: list[str] = []
        visiting: set[str] = set()

        def visit(identifier: str) -> None:
            if identifier in ordered:
                return
            if identifier in visiting:
                raise ValueError(f"Cyclic dependency: {identifier}")
            visiting.add(identifier)
            for dependency in self._version(identifier).dependencies:
                visit(dependency)
            visiting.remove(identifier)
            ordered.append(identifier)

        visit(package_id)
        return tuple(ordered)

    def compatible_with(self, package_id: str, platform: str) -> bool:
        """Return whether a release declares compatibility with a platform."""
        compatibility = self._version(package_id).compatibility
        return not compatibility or platform in compatibility

    def verify_integrity(
        self, package_id: str, payload: bytes, version: str | None = None
    ) -> bool:
        """Verify an artifact payload against its published SHA-256 checksum."""
        expected = self._version(package_id, version).checksum
        return bool(expected) and compare_digest(expected, sha256(payload).hexdigest())

    def verify_signature(
        self,
        package_id: str,
        payload: bytes,
        verifier: Callable[[bytes, str], bool],
        version: str | None = None,
    ) -> bool:
        """Delegate signature verification to an injected key-custody adapter."""
        signature = self._version(package_id, version).signature
        return bool(signature) and verifier(payload, signature)

    def download(self, package_id: str) -> MarketplacePackage:
        package = self._version(package_id)
        updated = replace(package, downloads=package.downloads + 1)
        self.packages[package_id][package.version] = updated
        self.download_log.append(package_id)
        self.metrics.increment("downloads_total")
        return updated

    def issue_license(self, license_: MarketplaceLicense) -> MarketplaceLicense:
        if license_.package_id not in self.packages:
            raise ValueError("Cannot license an unknown package.")
        if license_.seats is not None and license_.seats < 1:
            raise ValueError("Seat limits must be positive.")
        self.licenses[license_.license_id] = license_
        self.metrics.set("licenses_total", len(self.licenses))
        return license_

    def add_review(self, review: Review) -> Review:
        if review.package_id not in self.packages:
            raise ValueError("Cannot review an unknown package.")
        self.reviews[review.review_id] = review
        self.metrics.set("ratings_total", len(self.reviews))
        return review

    def moderate_review(self, review_id: str, *, approved: bool) -> Review:
        review = replace(self.reviews[review_id], moderated=True)
        if approved:
            self.reviews[review_id] = review
        else:
            del self.reviews[review_id]
        self.metrics.set("ratings_total", len(self.reviews))
        return review

    def rating(self, package_id: str) -> float | None:
        values = [
            item.rating
            for item in self.reviews.values()
            if item.package_id == package_id
        ]
        return None if not values else sum(values) / len(values)

    def purchase(self, invoice: Invoice) -> Invoice:
        if invoice.amount < 0:
            raise ValueError("Invoice amount must not be negative.")
        self.invoices[invoice.invoice_id] = invoice
        return invoice

    def record_usage(self, usage: Usage) -> Usage:
        if usage.used < 0 or usage.quota < 0 or usage.used > usage.quota:
            raise ValueError("Usage must remain within quota.")
        self.usage[(usage.account_id, usage.package_id)] = usage
        return usage

    def release_history(self, package_id: str) -> tuple[str, ...]:
        return tuple(self.packages.get(package_id, {}))

    def latest_packages(self) -> tuple[MarketplacePackage, ...]:
        return tuple(self._version(package_id) for package_id in self.packages)

    def _version(
        self, package_id: str, version: str | None = None
    ) -> MarketplacePackage:
        versions = self.packages.get(package_id)
        if not versions:
            raise ValueError(f"Unknown package: {package_id}")
        selected = version or next(reversed(versions))
        try:
            return versions[selected]
        except KeyError as error:
            raise ValueError(
                f"Unknown package version: {package_id}@{selected}"
            ) from error

    def _validate_dependencies(self, package: MarketplacePackage) -> None:
        self.dependency_graph(package.package_id)
        missing = [
            dependency
            for dependency in package.dependencies
            if dependency not in self.installed
        ]
        if missing:
            raise ValueError(f"Dependencies are not installed: {', '.join(missing)}")
