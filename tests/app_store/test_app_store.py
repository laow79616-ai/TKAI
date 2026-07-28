import hashlib

import pytest

from app_store import (
    ApplicationStatus,
    EnterpriseAppStore,
    License,
    LicenseKind,
    Review,
    Scope,
    Subscription,
)
from app_store.dashboard import SECTIONS, dashboard

SCOPE = Scope("tenant-a", "acme", "workspace-a")
ACTOR = "alice"
PERMISSIONS = {
    "install",
    "update",
    "uninstall",
    "publish",
    "review",
    "moderate",
    "manage_licenses",
    "manage_subscriptions",
}


def configured_store() -> EnterpriseAppStore:
    store = EnterpriseAppStore()
    store.security.grant(ACTOR, SCOPE, PERMISSIONS)
    store.create_publisher(
        {
            "id": "publisher-1",
            "name": "Acme AI",
            "organization": "acme",
            "owner": ACTOR,
            "tenant": "tenant-a",
            "workspace": "workspace-a",
            "verified": True,
            "signing_identity": "acme-signing",
            "support_contact": "support@example.test",
        }
    )
    store.create_application(
        {
            "id": "app-1",
            "name": "Knowledge Assistant",
            "description": "Enterprise RAG assistant",
            "version": "1.0.0",
            "publisher": "publisher-1",
            "category": "knowledge",
            "tags": ["rag", "verified"],
            "tenant": "tenant-a",
            "organization": "acme",
            "workspace": "workspace-a",
            "pricing": {"model": "subscription", "amount": 20},
        }
    )
    for status in ("submitted", "under_review", "approved", "published"):
        store.transition("app-1", SCOPE, status, ACTOR)
    return store


def package_payload(
    package_id: str = "package-1",
    version: str = "1.0.0",
    dependencies: tuple[str, ...] = (),
) -> dict[str, object]:
    artifact = f"oci://registry.example.test/acme/app:{version}"
    checksum = hashlib.sha256(artifact.encode()).hexdigest()
    signature = hashlib.sha256(f"acme-signing:{checksum}".encode()).hexdigest()
    return {
        "id": package_id,
        "application_id": "app-1",
        "version": version,
        "manifest": {"entrypoint": "application"},
        "dependencies": dependencies,
        "compatibility": {"platform": "tkai", "minimum_version": "3.1"},
        "checksum": checksum,
        "signature": signature,
        "artifact_reference": artifact,
        "size_bytes": 1024,
        "installation_instructions": ["Review permissions", "Activate application"],
        "upgrade_instructions": ["Create checkpoint", "Replace artifact"],
        "rollback_instructions": ["Restore previous artifact"],
    }


def test_catalog_lifecycle_publishers_and_isolation() -> None:
    store = configured_store()
    item = store.get_application("app-1", SCOPE)
    assert item.status is ApplicationStatus.PUBLISHED
    assert store.catalog(SCOPE, query="rag", category="knowledge") == (item,)
    assert store.publishers["publisher-1"].verified
    with pytest.raises(PermissionError):
        store.get_application("app-1", Scope("tenant-b", "acme", "workspace-a"))


def test_package_install_update_rollback_and_security() -> None:
    store = configured_store()
    first = store.add_package(package_payload(), ACTOR)
    second = store.add_package(package_payload("package-2", "2.0.0"), ACTOR)
    installed = store.install("installation-1", first.id, SCOPE, ACTOR, ("knowledge",))
    assert store.available_updates(installed.id) == (second,)
    assert store.update(installed.id, second.id, ACTOR).version == "2.0.0"
    assert store.rollback(installed.id, first.id, ACTOR).version == "1.0.0"
    assert (
        store.installation_action(installed.id, "enable", ACTOR).status.value
        == "enabled"
    )
    assert (
        store.installation_action(installed.id, "disable", ACTOR).status.value
        == "disabled"
    )
    assert store.metrics.snapshot()["app_store_updates_total"] == 2

    unsafe = package_payload("unsafe")
    unsafe["manifest"] = {"shell": "rm -rf /"}
    with pytest.raises(ValueError, match="shell"):
        store.add_package(unsafe, ACTOR)


def test_dependency_validation_and_integrity_failure() -> None:
    store = configured_store()
    item = package_payload()
    item["checksum"] = "invalid"
    with pytest.raises(ValueError, match="checksum"):
        store.add_package(item, ACTOR)
    dependent = package_payload("dependent", dependencies=("missing",))
    store.add_package(dependent, ACTOR)
    with pytest.raises(ValueError, match="Missing dependency"):
        store.install("installation-1", "dependent", SCOPE, ACTOR)
    assert store.metrics.snapshot()["app_store_install_failures_total"] == 1


def test_licenses_subscriptions_reviews_moderation_analytics_dashboard() -> None:
    store = configured_store()
    package = store.add_package(package_payload(), ACTOR)
    store.install("installation-1", package.id, SCOPE, ACTOR)
    license = store.add_license(
        License(
            "license-1",
            "app-1",
            SCOPE,
            LicenseKind.ENTERPRISE,
            active=True,
            seat_limit=100,
            tenant_limit=1,
        ),
        ACTOR,
    )
    assert store.validate_license(license.id, SCOPE)
    subscription = store.add_subscription(
        Subscription(
            "subscription-1",
            "app-1",
            SCOPE,
            "enterprise",
            ("support", "updates"),
            quota=1000,
            invoice_reference="invoice-provider:123",
        ),
        ACTOR,
    )
    assert store.cancel_subscription(subscription.id, ACTOR).cancelled
    review = store.add_review(
        Review("review-1", "app-1", SCOPE, ACTOR, 5, "Excellent", True),
        ACTOR,
    )
    assert store.moderate_review(review.id, ACTOR, "Thank you").moderated
    assert store.analytics(SCOPE)["ratings"] == 5
    view = dashboard(store, SCOPE)
    assert set(SECTIONS) <= set(view["sections"])
    assert view["metrics"]["app_store_reviews_total"] == 1


def test_permissions_and_secret_redaction() -> None:
    store = EnterpriseAppStore()
    with pytest.raises(PermissionError):
        store.security.require(ACTOR, SCOPE, "install")
    store.security.record("license.validation", ACTOR, SCOPE, {"license_key": "secret"})
    assert store.security.audit[-1]["details"] == {"license_key": "[REDACTED]"}
