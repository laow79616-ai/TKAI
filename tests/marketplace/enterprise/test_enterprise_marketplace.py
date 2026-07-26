"""Sprint-9 Enterprise Marketplace validation."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from marketplace import (
    EnterpriseMarketplace,
    EnterprisePublisherProfile,
    Invoice,
    LicenseKind,
    MarketplaceLicense,
    MarketplacePackage,
    Review,
    StoreKind,
    Usage,
)
from marketplace.api import MarketplaceApi, register_marketplace_routes


def package(version: str = "1.0.0", **changes: object) -> MarketplacePackage:
    values: dict[str, object] = {
        "package_id": "acme.agent",
        "name": "Acme Agent",
        "kind": StoreKind.AGENT,
        "publisher_id": "acme",
        "version": version,
        "category": "automation",
        "tags": frozenset({"agent", "enterprise"}),
        "compatibility": frozenset({"tkai>=2.3"}),
        "featured": True,
    }
    values.update(changes)
    return MarketplacePackage(**values)  # type: ignore[arg-type]


def store() -> EnterpriseMarketplace:
    result = EnterpriseMarketplace()
    result.register_publisher(
        EnterprisePublisherProfile(
            "acme", "Acme Corp", "Acme", owners=("owner@acme.test",)
        )
    )
    result.verify_publisher("acme")
    result.publish(package())
    return result


def test_catalog_search_filter_categories_tags_featured_verified_and_trending() -> None:
    marketplace = store()
    marketplace.download("acme.agent")
    assert marketplace.search(
        "agent",
        category="automation",
        tag="enterprise",
        kind=StoreKind.AGENT,
        featured=True,
        verified=True,
        trending=True,
    )[0].downloads == 1
    assert marketplace.categories() == ("automation",)
    assert marketplace.tags() == ("agent", "enterprise")
    assert marketplace.stores()["agent"][0].package_id == "acme.agent"


def test_publisher_ownership_verification_and_release_history() -> None:
    marketplace = store()
    assert marketplace.publishers["acme"].verified
    assert marketplace.publishers["acme"].owners == ("owner@acme.test",)
    marketplace.publish(package("2.0.0"))
    assert marketplace.release_history("acme.agent") == ("1.0.0", "2.0.0")


def test_package_install_upgrade_rollback_dependencies_and_compatibility() -> None:
    marketplace = store()
    marketplace.publish(package("2.0.0"))
    assert marketplace.install("acme.agent", "1.0.0").version == "1.0.0"
    assert marketplace.upgrade("acme.agent", "2.0.0").version == "2.0.0"
    assert marketplace.rollback("acme.agent").version == "1.0.0"
    assert marketplace.dependency_graph("acme.agent") == ("acme.agent",)
    assert "tkai>=2.3" in marketplace.search()[0].compatibility
    assert marketplace.compatible_with("acme.agent", "tkai>=2.3")

    marketplace.publish(
        package(
            package_id="acme.workflow",
            name="Acme Workflow",
            kind=StoreKind.WORKFLOW,
            dependencies=("missing",),
        )
    )
    with pytest.raises(ValueError, match="Unknown package"):
        marketplace.install("acme.workflow")


def test_package_integrity_and_signature_use_explicit_artifact_adapters() -> None:
    payload = b"enterprise artifact"
    checksum = sha256(payload).hexdigest()
    marketplace = EnterpriseMarketplace()
    marketplace.register_publisher(
        EnterprisePublisherProfile(
            "acme",
            "Acme Corp",
            "Acme",
            verified=True,
            signing_key_id="key-1",
        )
    )
    marketplace.publish(package(checksum=checksum, signature="signed-value"))

    assert marketplace.verify_integrity("acme.agent", payload)
    assert not marketplace.verify_integrity("acme.agent", b"tampered")
    assert marketplace.verify_signature(
        "acme.agent",
        payload,
        lambda artifact, signature: artifact == payload
        and signature == "signed-value",
    )


@pytest.mark.parametrize("kind", list(LicenseKind))
def test_all_license_kinds_and_seat_limits(kind: LicenseKind) -> None:
    marketplace = store()
    license_ = marketplace.issue_license(
        MarketplaceLicense(
            f"license-{kind.value}",
            "acme.agent",
            kind,
            seats=25,
            offline=kind is LicenseKind.OFFLINE,
        )
    )
    assert license_.seats == 25
    assert marketplace.metrics.snapshot()["licenses_total"] == 1

    with pytest.raises(ValueError, match="positive"):
        marketplace.issue_license(
            MarketplaceLicense("invalid", "acme.agent", kind, seats=0)
        )


def test_reviews_moderation_ratings_billing_quota_and_metrics() -> None:
    marketplace = store()
    marketplace.add_review(
        Review("review-1", "acme.agent", "buyer", 5, "Excellent", True)
    )
    assert marketplace.rating("acme.agent") == 5
    assert marketplace.moderate_review("review-1", approved=True).moderated
    assert marketplace.purchase(
        Invoice("invoice-1", "account-1", "acme.agent", 9900)
    ).currency == "USD"
    assert marketplace.record_usage(
        Usage("account-1", "acme.agent", 4, 10)
    ).used == 4
    with pytest.raises(ValueError, match="quota"):
        marketplace.record_usage(Usage("account-1", "acme.agent", 11, 10))

    metrics = marketplace.metrics.render_prometheus()
    for name in marketplace.metrics.NAMES:
        assert f"tkai_marketplace_{name}" in metrics


class FakeApp:
    def __init__(self) -> None:
        self.routes: list[tuple[str, tuple[str, ...]]] = []

    def add_api_route(
        self,
        path: str,
        _endpoint: object,
        *,
        methods: list[str],
        tags: list[str],
    ) -> None:
        assert tags == ["marketplace"]
        self.routes.append((path, tuple(methods)))


def test_api_and_dashboard_contracts() -> None:
    marketplace = store()
    api = MarketplaceApi(marketplace)
    assert api.catalog()["total"] == 1
    assert api.publishers()["total"] == 1

    app = FakeApp()
    register_marketplace_routes(app, marketplace)
    assert [path for path, _methods in app.routes] == [
        "/marketplace",
        "/packages",
        "/publishers",
        "/licenses",
        "/reviews",
        "/downloads",
    ]

    root = Path(__file__).parents[3]
    routes = (root / "dashboard/frontend/src/App.tsx").read_text(encoding="utf-8")
    pages = (root / "dashboard/frontend/src/pages.tsx").read_text(encoding="utf-8")
    dashboard_routes = (
        "marketplace",
        "publishers",
        "packages",
        "downloads",
        "licenses",
        "reviews",
    )
    for name in dashboard_routes:
        assert f'path="/{name}"' in routes
    assert "MarketplacePage" in pages
