"""Enterprise App Store orchestration."""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from .metrics import AppStoreMetrics
from .models import (
    ApplicationStatus,
    Compatibility,
    Installation,
    InstallationStatus,
    License,
    LicenseKind,
    Package,
    Pricing,
    Publisher,
    ReleaseChannel,
    Review,
    Scope,
    StoreApplication,
    Subscription,
    Visibility,
)
from .security import SecurityPolicy

TRANSITIONS = {
    ApplicationStatus.DRAFT: {ApplicationStatus.SUBMITTED, ApplicationStatus.DELETED},
    ApplicationStatus.SUBMITTED: {
        ApplicationStatus.UNDER_REVIEW,
        ApplicationStatus.DRAFT,
    },
    ApplicationStatus.UNDER_REVIEW: {
        ApplicationStatus.APPROVED,
        ApplicationStatus.DRAFT,
    },
    ApplicationStatus.APPROVED: {
        ApplicationStatus.PUBLISHED,
        ApplicationStatus.SUSPENDED,
    },
    ApplicationStatus.PUBLISHED: {
        ApplicationStatus.SUSPENDED,
        ApplicationStatus.DEPRECATED,
    },
    ApplicationStatus.SUSPENDED: {
        ApplicationStatus.PUBLISHED,
        ApplicationStatus.ARCHIVED,
    },
    ApplicationStatus.DEPRECATED: {ApplicationStatus.ARCHIVED},
    ApplicationStatus.ARCHIVED: {ApplicationStatus.DELETED},
    ApplicationStatus.DELETED: set(),
}


def _compatibility(value: dict[str, Any] | None) -> Compatibility:
    data = value or {}
    return Compatibility(
        platform=str(data.get("platform", "tkai")),
        minimum_version=str(data.get("minimum_version", "3.1")),
        maximum_version=data.get("maximum_version"),
        architectures=tuple(data.get("architectures", ("amd64", "arm64"))),
    )


class EnterpriseAppStore:
    def __init__(self) -> None:
        self.applications: dict[str, StoreApplication] = {}
        self.publishers: dict[str, Publisher] = {}
        self.packages: dict[str, Package] = {}
        self.installations: dict[str, Installation] = {}
        self.licenses: dict[str, License] = {}
        self.subscriptions: dict[str, Subscription] = {}
        self.reviews: dict[str, Review] = {}
        self.metrics = AppStoreMetrics()
        self.security = SecurityPolicy()

    def create_publisher(self, payload: dict[str, Any]) -> Publisher:
        item = Publisher(
            id=str(payload["id"]),
            name=str(payload["name"]),
            organization=str(payload["organization"]),
            owner=str(payload["owner"]),
            tenant=str(payload["tenant"]),
            workspace=str(payload["workspace"]),
            verified=bool(payload.get("verified", False)),
            signing_identity=payload.get("signing_identity"),
            support_contact=payload.get("support_contact"),
        )
        if item.id in self.publishers:
            raise ValueError("Publisher already exists.")
        self.publishers[item.id] = item
        self.metrics.increment("app_store_publishers_total")
        return item

    def create_application(self, payload: dict[str, Any]) -> StoreApplication:
        item = StoreApplication(
            id=str(payload["id"]),
            name=str(payload["name"]),
            description=str(payload.get("description", "")),
            version=str(payload["version"]),
            publisher=str(payload["publisher"]),
            category=str(payload.get("category", "general")),
            tenant=str(payload["tenant"]),
            organization=str(payload["organization"]),
            workspace=str(payload["workspace"]),
            tags=tuple(str(value) for value in payload.get("tags", ())),
            icon_reference=payload.get("icon_reference"),
            screenshots=tuple(payload.get("screenshots", ())),
            visibility=Visibility(str(payload.get("visibility", "private"))),
            compatibility=_compatibility(payload.get("compatibility")),
            license=LicenseKind(str(payload.get("license", "open_source"))),
            pricing=Pricing(**dict(payload.get("pricing", {}))),
            metadata=dict(payload.get("metadata", {})),
        )
        if item.id in self.applications:
            raise ValueError("Application already exists.")
        publisher = self.publishers.get(item.publisher)
        if publisher is None or publisher.scope != item.scope:
            raise ValueError("A publisher in the same scope is required.")
        self.applications[item.id] = item
        self.metrics.increment("app_store_applications_total")
        return item

    def get_application(self, application_id: str, scope: Scope) -> StoreApplication:
        item = self.applications[application_id]
        if item.scope != scope:
            raise PermissionError(
                "Tenant, organization, or workspace isolation violation."
            )
        return item

    def transition(
        self, application_id: str, scope: Scope, status: str, actor: str
    ) -> StoreApplication:
        item = self.get_application(application_id, scope)
        target = ApplicationStatus(status)
        if target not in TRANSITIONS[item.status]:
            raise ValueError(
                f"Invalid transition: {item.status.value} -> {target.value}"
            )
        permission = (
            "moderate"
            if target in {ApplicationStatus.APPROVED, ApplicationStatus.SUSPENDED}
            else "publish"
        )
        self.security.require(actor, scope, permission)
        updated = replace(item, status=target)
        self.applications[item.id] = updated
        self.security.record(
            "application.lifecycle",
            actor,
            scope,
            {"application": application_id, "status": status},
        )
        return updated

    def catalog(
        self,
        scope: Scope,
        query: str = "",
        category: str | None = None,
        tags: tuple[str, ...] = (),
        featured: bool | None = None,
        verified: bool | None = None,
    ) -> tuple[StoreApplication, ...]:
        values = tuple(
            item
            for item in self.applications.values()
            if item.scope == scope and item.status is ApplicationStatus.PUBLISHED
        )
        query = query.casefold()
        if query:
            values = tuple(
                item
                for item in values
                if query
                in f"{item.name} {item.description} {' '.join(item.tags)}".casefold()
            )
        if category:
            values = tuple(item for item in values if item.category == category)
        if tags:
            values = tuple(item for item in values if set(tags) <= set(item.tags))
        if featured is not None:
            values = tuple(item for item in values if item.featured is featured)
        if verified is not None:
            values = tuple(item for item in values if item.verified is verified)
        return values

    def add_package(self, payload: dict[str, Any], actor: str) -> Package:
        application = self.applications[str(payload["application_id"])]
        self.security.require(actor, application.scope, "publish")
        publisher = self.publishers[application.publisher]
        if not publisher.verified or not publisher.signing_identity:
            raise ValueError("Verified publisher and signing identity are required.")
        item = Package(
            id=str(payload["id"]),
            application_id=application.id,
            version=str(payload["version"]),
            manifest=dict(payload.get("manifest", {})),
            dependencies=tuple(payload.get("dependencies", ())),
            compatibility=_compatibility(payload.get("compatibility")),
            checksum=str(payload["checksum"]),
            signature=str(payload["signature"]),
            artifact_reference=str(payload["artifact_reference"]),
            installation_instructions=tuple(
                payload.get("installation_instructions", ())
            ),
            upgrade_instructions=tuple(payload.get("upgrade_instructions", ())),
            rollback_instructions=tuple(payload.get("rollback_instructions", ())),
            size_bytes=int(payload.get("size_bytes", 0)),
            channel=ReleaseChannel(str(payload.get("channel", "stable"))),
        )
        self.security.validate_package(item, publisher.signing_identity)
        self.packages[item.id] = item
        self.publishers[publisher.id] = replace(
            publisher, release_history=publisher.release_history + (item.id,)
        )
        return item

    def install(
        self,
        installation_id: str,
        package_id: str,
        scope: Scope,
        actor: str,
        permissions: tuple[str, ...] = (),
    ) -> Installation:
        self.security.require(actor, scope, "install")
        package = self.packages[package_id]
        application = self.get_application(package.application_id, scope)
        publisher = self.publishers[application.publisher]
        try:
            self.security.validate_package(package, publisher.signing_identity or "")
            self._validate_dependencies(package, set(), 0)
            if package.compatibility.platform != "tkai":
                raise ValueError("Package platform is incompatible.")
        except ValueError:
            self.metrics.increment("app_store_install_failures_total")
            raise
        item = Installation(
            installation_id,
            application.id,
            package.id,
            package.version,
            scope,
            InstallationStatus.INSTALLED,
            permissions,
            release_channel=package.channel,
        )
        self.installations[item.id] = item
        self.metrics.increment("app_store_installs_total")
        self._active_installation_gauge()
        return item

    def installation_action(
        self, installation_id: str, action: str, actor: str
    ) -> Installation:
        item = self.installations[installation_id]
        permission = "uninstall" if action == "uninstall" else "update"
        self.security.require(actor, item.scope, permission)
        statuses = {
            "enable": InstallationStatus.ENABLED,
            "disable": InstallationStatus.DISABLED,
            "uninstall": InstallationStatus.UNINSTALLED,
        }
        if action not in statuses:
            raise ValueError("Unsupported installation action.")
        updated = replace(item, status=statuses[action])
        self.installations[item.id] = updated
        self._active_installation_gauge()
        return updated

    def update(self, installation_id: str, package_id: str, actor: str) -> Installation:
        current = self.installations[installation_id]
        self.security.require(actor, current.scope, "update")
        package = self.packages[package_id]
        if package.application_id != current.application_id:
            raise ValueError("Update package belongs to another application.")
        if current.pinned_version and current.pinned_version != package.version:
            raise ValueError("Installation version is pinned.")
        if package.channel != current.release_channel:
            raise ValueError("Update is outside the selected release channel.")
        publisher = self.publishers[self.applications[current.application_id].publisher]
        self.security.validate_package(package, publisher.signing_identity or "")
        updated = replace(current, package_id=package.id, version=package.version)
        self.installations[current.id] = updated
        self.metrics.increment("app_store_updates_total")
        return updated

    def rollback(
        self, installation_id: str, package_id: str, actor: str
    ) -> Installation:
        return self.update(installation_id, package_id, actor)

    def add_license(self, license: License, actor: str) -> License:
        self.security.require(actor, license.scope, "manage_licenses")
        self.licenses[license.id] = license
        return license

    def validate_license(self, license_id: str, scope: Scope) -> bool:
        item = self.licenses[license_id]
        if item.scope != scope:
            raise PermissionError("License scope mismatch.")
        self.metrics.increment("app_store_license_validations_total")
        return item.active

    def add_subscription(self, subscription: Subscription, actor: str) -> Subscription:
        self.security.require(actor, subscription.scope, "manage_subscriptions")
        self.subscriptions[subscription.id] = subscription
        return subscription

    def cancel_subscription(self, subscription_id: str, actor: str) -> Subscription:
        item = self.subscriptions[subscription_id]
        self.security.require(actor, item.scope, "manage_subscriptions")
        updated = replace(item, cancelled=True)
        self.subscriptions[item.id] = updated
        return updated

    def add_review(self, review: Review, actor: str) -> Review:
        self.security.require(actor, review.scope, "review")
        installed = any(
            item.application_id == review.application_id
            and item.scope == review.scope
            and item.status is not InstallationStatus.UNINSTALLED
            for item in self.installations.values()
        )
        if review.verified_installation and not installed:
            raise ValueError("Verified review requires an installation.")
        self.reviews[review.id] = review
        self.metrics.increment("app_store_reviews_total")
        return review

    def moderate_review(
        self, review_id: str, actor: str, publisher_reply: str | None = None
    ) -> Review:
        item = self.reviews[review_id]
        self.security.require(actor, item.scope, "moderate")
        updated = replace(item, moderated=True, publisher_reply=publisher_reply)
        self.reviews[item.id] = updated
        return updated

    def analytics(self, scope: Scope) -> dict[str, float]:
        app_ids = {
            item.id for item in self.applications.values() if item.scope == scope
        }
        ratings = [
            item.rating
            for item in self.reviews.values()
            if item.application_id in app_ids
        ]
        installs = [item for item in self.installations.values() if item.scope == scope]
        metrics = self.metrics.snapshot()
        return {
            "views": 0,
            "downloads": float(len(installs)),
            "installs": float(len(installs)),
            "active_installations": float(
                sum(
                    item.status is not InstallationStatus.UNINSTALLED
                    for item in installs
                )
            ),
            "updates": metrics["app_store_updates_total"],
            "failures": metrics["app_store_install_failures_total"],
            "ratings": sum(ratings) / len(ratings) if ratings else 0,
            "conversion": 0,
        }

    def available_updates(self, installation_id: str) -> tuple[Package, ...]:
        item = self.installations[installation_id]
        if item.pinned_version:
            return ()
        return tuple(
            package
            for package in self.packages.values()
            if package.application_id == item.application_id
            and package.version != item.version
            and package.channel == item.release_channel
        )

    def _validate_dependencies(
        self, package: Package, visited: set[str], depth: int
    ) -> None:
        if depth > self.security.maximum_dependency_depth:
            raise ValueError("Dependency depth exceeds the configured bound.")
        if package.id in visited:
            raise ValueError("Circular package dependency.")
        visited.add(package.id)
        for dependency_id in package.dependencies:
            dependency = self.packages.get(dependency_id)
            if dependency is None:
                raise ValueError(f"Missing dependency: {dependency_id}")
            self._validate_dependencies(dependency, set(visited), depth + 1)

    def _active_installation_gauge(self) -> None:
        active = sum(
            item.status is not InstallationStatus.UNINSTALLED
            for item in self.installations.values()
        )
        self.metrics.gauge("app_store_active_installations", active)
