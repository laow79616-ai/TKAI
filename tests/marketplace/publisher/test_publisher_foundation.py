"""Offline Publisher Foundation regression tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from marketplace.publisher import (
    Publisher,
    PublisherCapability,
    PublisherFactory,
    PublisherOrganization,
    PublisherPolicy,
    PublisherProfile,
    PublisherRegistry,
    PublisherTier,
    PublisherTrust,
    PublisherVerification,
    ReferencePublisherService,
)
from marketplace.publisher.errors import PublisherConflictError, PublisherNotFoundError


def _publisher(
    publisher_id: str, tier: PublisherTier = PublisherTier.COMMUNITY
) -> Publisher:
    return Publisher(
        publisher_id,
        PublisherProfile("Publisher", metadata={"source": "test"}),
        tier,
        PublisherOrganization("organization", "Organization"),
        frozenset({PublisherCapability("plugins")}),
    )


def test_publisher_models_are_immutable_defensive_and_serializable() -> None:
    """Publisher descriptors carry no credentials and freeze caller metadata."""
    source = {"source": "test"}
    publisher = Publisher("publisher", PublisherProfile("Publisher", metadata=source))
    source["source"] = "changed"

    assert publisher.profile.metadata == {"source": "test"}
    assert publisher.to_dict()["tier"] == "community"
    with pytest.raises(FrozenInstanceError):
        publisher.publisher_id = "other"
    with pytest.raises(TypeError):
        publisher.profile.metadata["source"] = "changed"


def test_factory_policy_and_reference_service_are_explicit_and_offline() -> None:
    """Factory and policy work entirely on caller-owned local descriptors."""
    factory = PublisherFactory()
    official = factory.create("official", "Official", tier=PublisherTier.OFFICIAL)
    validation = PublisherPolicy().validate_creation(official)
    assert validation.valid
    assert validation.warnings == (
        "Official or Enterprise publisher has no organization.",
    )

    service = ReferencePublisherService()
    service.create("community", "Community")
    assert service.publisher("community").tier is PublisherTier.COMMUNITY
    service.close()
    service.close()
    assert service.publishers() == ()


def test_publisher_registry_is_thread_safe_stable_and_isolated() -> None:
    """Concurrent local declarations are stable and duplicate errors are explicit."""
    registry = PublisherRegistry()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: registry.register(_publisher(str(index))), range(8)
            )
        )
    assert [publisher.publisher_id for publisher in registry.snapshot()] == [
        str(index) for index in range(8)
    ]
    with pytest.raises(PublisherConflictError):
        registry.register(_publisher("0"))
    with pytest.raises(PublisherNotFoundError):
        registry.get("missing")


def test_tiers_and_verification_trust_are_declaration_only_contracts() -> None:
    """All documented tiers and future verification boundaries are import-only."""
    assert {tier.value for tier in PublisherTier} == {
        "community",
        "verified",
        "official",
        "enterprise",
    }
    assert getattr(PublisherVerification, "_is_protocol", False)
    assert getattr(PublisherTrust, "_is_protocol", False)


def test_publisher_documentation_keeps_foundation_reference_only() -> None:
    """Documentation rules out registry download, installation, and network work."""
    document = (Path(__file__).parents[3] / "docs" / "Publisher.md").read_text(
        encoding="utf-8"
    )
    assert "No network" in document
    assert "package download" in document
    assert "installation" in document
