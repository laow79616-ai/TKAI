"""Offline regression tests for Marketplace publication contracts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from marketplace.models import PackageDependency, PackageVersion
from marketplace.package_catalog import (
    PackageCategory,
    PackageCompatibility,
    PackageManifest,
    PackageMetadata,
    PackageTag,
)
from marketplace.publication import (
    PublicationDecision,
    PublicationId,
    PublicationLifecycle,
    PublicationManifest,
    PublicationMetadata,
    PublicationPolicy,
    PublicationRequest,
    PublicationStatus,
    PublicationValidator,
    ReferencePublicationService,
    ReferencePublicationValidator,
)
from marketplace.publication.errors import (
    PublicationClosedError,
    PublicationConflictError,
    PublicationNotFoundError,
    PublicationStateError,
    PublicationValidationError,
)
from marketplace.publisher import Publisher, PublisherProfile, PublisherTier


def _publisher(tier: PublisherTier = PublisherTier.COMMUNITY) -> Publisher:
    return Publisher("publisher", PublisherProfile("Publisher"), tier)


def _manifest(
    package_id: str = "package",
    *,
    version: PackageVersion | None = None,
    tags: frozenset[PackageTag] = frozenset({PackageTag("reference")}),
    compatibility: PackageCompatibility | None = None,
    dependencies: tuple[PackageDependency, ...] = (PackageDependency("base"),),
) -> PackageManifest:
    return PackageManifest(
        package_id,
        "publisher",
        "Package",
        "Reference package",
        PackageVersion(1) if version is None else version,
        PackageCategory.PLUGIN,
        tags,
        PackageCompatibility(runtime="1.3") if compatibility is None else compatibility,
        dependencies,
        PackageMetadata("Reference"),
    )


def _request(
    publication_id: str = "publication",
    *,
    manifest: PackageManifest | None = None,
    metadata: dict[str, str] | None = None,
) -> PublicationRequest:
    return PublicationRequest(
        PublicationId(publication_id),
        "publisher",
        _manifest() if manifest is None else manifest,
        metadata=PublicationMetadata({} if metadata is None else metadata),
    )


def test_publication_models_are_immutable_json_safe_and_defensive() -> None:
    """Publication metadata is caller-owned and all result fields serialize stably."""
    source = {"source": "test"}
    request = _request(metadata=source)
    source["source"] = "changed"
    publication_manifest = PublicationManifest(_publisher(), request.package_manifest)

    assert request.metadata.values == {"source": "test"}
    assert publication_manifest.to_dict()["package_manifest"]["package_id"] == "package"
    with pytest.raises(FrozenInstanceError):
        request.publisher_id = "other"
    with pytest.raises(TypeError):
        request.metadata.values["source"] = "changed"


def test_request_manifest_and_validator_contracts_are_explicit() -> None:
    """Request shape checks do not query publisher, Catalog, or Registry state."""
    assert getattr(PublicationValidator, "_is_protocol", False)
    with pytest.raises(ValueError):
        PublicationRequest(PublicationId("bad"), "other", _manifest())

    validator = ReferencePublicationValidator(_publisher())
    result = validator.validate(_request(), PublicationPolicy())
    assert result.decision is PublicationDecision.ACCEPT
    assert result.issues == ()


def test_policy_evaluation_has_deterministic_local_issues() -> None:
    """Strict policy reports sorted structural issues without trust enforcement."""
    manifest = _manifest(
        version=PackageVersion(1, prerelease="rc1"),
        tags=frozenset({PackageTag("a"), PackageTag("b")}),
        compatibility=PackageCompatibility(),
        dependencies=(),
    )
    request = _request(manifest=manifest, metadata={"a": "1", "b": "2"})
    policy = PublicationPolicy(
        allow_community_submission=False,
        allow_prerelease=False,
        allow_empty_dependencies=False,
        allow_unknown_compatibility_targets=False,
        max_tag_count=1,
        max_metadata_entries=1,
    )
    result = ReferencePublicationValidator(_publisher()).validate(request, policy)
    assert result.decision is PublicationDecision.REJECT
    assert [issue.code for issue in result.issues] == sorted(
        issue.code for issue in result.issues
    )


def test_lifecycle_allows_only_documented_transitions() -> None:
    """Illegal transitions raise without a mutable lifecycle side effect."""
    lifecycle = PublicationLifecycle()
    assert lifecycle.can_transition(
        PublicationStatus.DRAFT, PublicationStatus.SUBMITTED
    )
    assert (
        lifecycle.transition(PublicationStatus.SUBMITTED, PublicationStatus.VALIDATING)
        is PublicationStatus.VALIDATING
    )
    with pytest.raises(PublicationStateError):
        lifecycle.transition(PublicationStatus.ACCEPTED, PublicationStatus.DRAFT)


def test_reference_service_submit_validate_accept_and_reject_paths() -> None:
    """Reference flow stores local snapshots without catalog registration."""
    accepted = ReferencePublicationService(_publisher())
    accepted.submit(_request("accepted"))
    assert accepted.validate("accepted").decision is PublicationDecision.ACCEPT
    assert accepted.accept("accepted").status is PublicationStatus.ACCEPTED

    rejected = ReferencePublicationService(
        _publisher(), policy=PublicationPolicy(allow_community_submission=False)
    )
    rejected.submit(_request("rejected"))
    assert rejected.validate("rejected").decision is PublicationDecision.REJECT
    assert rejected.reject("rejected").status is PublicationStatus.REJECTED
    with pytest.raises(PublicationValidationError):
        rejected.accept("rejected")


def test_duplicate_withdraw_missing_and_snapshot_behavior_are_stable() -> None:
    """Duplicate coordinates reject predictably and snapshots are immutable tuples."""
    service = ReferencePublicationService(_publisher())
    service.submit(_request("one"))
    with pytest.raises(PublicationConflictError):
        service.submit(_request("two"))
    assert service.withdraw("one").status is PublicationStatus.WITHDRAWN
    with pytest.raises(PublicationNotFoundError):
        service.get("missing")
    assert isinstance(service.snapshot(), tuple)


def test_reference_service_is_thread_safe_isolated_and_closed_explicitly() -> None:
    """Bounded local operations have no cross-instance state or background worker."""
    service = ReferencePublicationService(_publisher())
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: service.submit(
                    _request(str(index), manifest=_manifest(str(index)))
                ),
                range(8),
            )
        )
    assert len(service.snapshot()) == 8
    assert ReferencePublicationService(_publisher()).snapshot() == ()
    service.close()
    service.close()
    with pytest.raises(PublicationClosedError):
        service.list()


def test_publication_documentation_states_explicit_non_goals() -> None:
    """Documentation excludes all remote and installation behavior from this Sprint."""
    document = (Path(__file__).parents[3] / "docs" / "Publication.md").read_text(
        encoding="utf-8"
    )
    for phrase in (
        "Reference Only",
        "Offline Only",
        "No artifact upload",
        "No remote registry",
        "No authentication",
        "No package installation",
    ):
        assert phrase in document
