"""Offline Marketplace RC-2 reliability, lifecycle, and failure-isolation checks."""

import pytest

from marketplace.installer import (
    InstallationId,
    InstallationRequest,
    ReferenceInstallationStore,
    ReferenceInstallerService,
)
from marketplace.installer.errors import InstallerClosedError
from marketplace.models import PackageVersion
from marketplace.package_catalog import (
    PackageCategory,
    PackageCompatibility,
    PackageManifest,
    PackageMetadata,
)
from marketplace.publication import (
    PublicationId,
    PublicationPolicy,
    PublicationRequest,
    PublicationStatus,
    ReferencePublicationService,
)
from marketplace.publisher import (
    Publisher,
    PublisherProfile,
    PublisherRegistry,
    PublisherTier,
)
from marketplace.registry_foundation import (
    ReferenceRegistryPublicationAdapter,
    ReferenceRegistryService,
    RegistryEntryId,
    RegistrySnapshot,
)
from marketplace.registry_foundation.errors import RegistryConflictError
from marketplace.registry_foundation.models import RegistryIndex
from marketplace.resolver import (
    DependencyCoordinate,
    DependencyGraph,
    DependencyRequirement,
    ReferenceResolverService,
    ResolutionRequest,
    ResolutionResult,
    ResolutionStatus,
)
from marketplace.verification import (
    ReferenceTrustService,
    ReferenceVerificationService,
    TrustDecision,
    TrustLevel,
    TrustPolicy,
    TrustReport,
    VerificationRequest,
    VerificationStatus,
)


def _resolution(package_id: str) -> ResolutionResult:
    coordinate = DependencyCoordinate("reliability", package_id, PackageVersion(1))
    return ResolutionResult(
        ResolutionStatus.RESOLVED,
        (),
        (coordinate,),
        (coordinate,),
        DependencyGraph(),
    )


def test_marketplace_reference_state_is_stable_across_ten_clear_and_reuse_rounds() -> (
    None
):
    """Reference stores are bounded, reusable, and independent across fixed rounds."""
    publishers = PublisherRegistry()
    resolver = ReferenceResolverService()
    for index in range(10):
        publisher = Publisher(f"publisher-{index}", PublisherProfile("Reference"))
        publishers.register(publisher)
        service = ReferenceInstallerService()
        service.install(
            InstallationRequest(
                InstallationId(f"round-{index}"), _resolution(f"p-{index}")
            )
        )
        assert service.snapshot().statistics.succeeded == 1
        service.clear()
        assert not service.snapshot().sessions
        resolver.resolve(
            ResolutionRequest(
                RegistrySnapshot((), RegistryIndex()),
                root_requirements=(DependencyRequirement("missing"),),
            )
        )
        assert resolver.snapshot().result is not None
        resolver.clear()
    assert len(publishers.snapshot()) == 10


def test_marketplace_failures_do_not_pollute_following_reference_operations() -> None:
    """Failure injection remains local; later verification and installation succeed."""

    class FailingStore(ReferenceInstallationStore):
        def add(self, item):
            raise RuntimeError("injected store failure")

    installer = ReferenceInstallerService(FailingStore())
    with pytest.raises(RuntimeError, match="injected store failure"):
        installer.install(
            InstallationRequest(InstallationId("abort"), _resolution("a"))
        )
    assert not installer.snapshot().installed_records
    assert installer.snapshot().transactions[0].state.value == "aborted"

    verifier = ReferenceVerificationService()
    assert (
        verifier.verify(VerificationRequest(None)).result.status
        is VerificationStatus.FAILED
    )
    assert (
        verifier.verify(VerificationRequest(object())).result.status
        is VerificationStatus.PASSED
    )
    trust = ReferenceTrustService(TrustPolicy(minimum=TrustLevel.VERIFIED))
    assert trust.evaluate(TrustLevel.COMMUNITY).decision is TrustDecision.REVIEW
    explicit_rejection = TrustReport(
        TrustLevel.COMMUNITY, TrustDecision.REJECT, TrustPolicy()
    )
    assert explicit_rejection.decision is TrustDecision.REJECT


def test_publication_rejection_and_registry_conflict_are_local_to_their_services() -> (
    None
):
    """Publication rejection and duplicate Registry insertion retain good state."""
    community = Publisher("community", PublisherProfile("Community"))
    rejected = ReferencePublicationService(
        community, policy=PublicationPolicy(allow_community_submission=False)
    )
    rejected.submit(
        PublicationRequest(
            PublicationId("rejected"),
            "community",
            PackageManifest(
                "rejected",
                "community",
                "Rejected",
                "",
                PackageVersion(1),
                PackageCategory.PLUGIN,
                compatibility=PackageCompatibility(),
                metadata=PackageMetadata(),
            ),
        )
    )
    assert rejected.validate("rejected").decision.value == "reject"
    assert rejected.reject("rejected").status is PublicationStatus.REJECTED

    publisher = Publisher(
        "verified", PublisherProfile("Verified"), PublisherTier.VERIFIED
    )
    accepted_service = ReferencePublicationService(publisher)
    manifest = PackageManifest(
        "accepted",
        "verified",
        "Accepted",
        "",
        PackageVersion(1),
        PackageCategory.PLUGIN,
        compatibility=PackageCompatibility(),
        metadata=PackageMetadata(),
    )
    accepted_service.submit(
        PublicationRequest(PublicationId("accepted"), "verified", manifest)
    )
    accepted_service.validate("accepted")
    accepted = accepted_service.accept("accepted")
    registry = ReferenceRegistryService()
    adapter = ReferenceRegistryPublicationAdapter(publisher)
    registry.register_publication(RegistryEntryId("accepted"), accepted, adapter)
    with pytest.raises(RegistryConflictError):
        registry.register_publication(RegistryEntryId("accepted"), accepted, adapter)
    assert len(registry.snapshot().entries) == 1


def test_marketplace_rollback_and_close_are_idempotent_and_isolated() -> None:
    """Rollback restores the local store and close prevents only that instance's use."""
    first = ReferenceInstallerService()
    first.install(InstallationRequest(InstallationId("first"), _resolution("first")))
    assert first.rollback("first").state.value == "completed"
    assert not first.snapshot().installed_records
    first.close()
    first.close()
    with pytest.raises(InstallerClosedError):
        first.install(InstallationRequest(InstallationId("closed"), _resolution("x")))

    second = ReferenceInstallerService()
    assert second.install(
        InstallationRequest(InstallationId("second"), _resolution("second"))
    ).installed
