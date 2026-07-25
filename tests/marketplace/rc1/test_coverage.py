"""Offline RC-1 coverage for explicit Marketplace Foundation collaboration."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from marketplace.installer import (
    InstallationId,
    InstallationRequest,
    InstallationStatus,
    ReferenceInstallationStore,
    ReferenceInstallerService,
)
from marketplace.installer.errors import InstallerClosedError, InstallerConflictError
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
from marketplace.publisher import Publisher, PublisherProfile, PublisherTier
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
    VerificationRequest,
)


def _coordinates(*names: str) -> tuple[DependencyCoordinate, ...]:
    return tuple(
        DependencyCoordinate("rc1-publisher", name, PackageVersion(1)) for name in names
    )


def _resolved(*names: str) -> ResolutionResult:
    coordinates = _coordinates(*names)
    return ResolutionResult(
        ResolutionStatus.RESOLVED,
        (),
        coordinates,
        coordinates,
        DependencyGraph(),
    )


def _manifest(package_id: str) -> PackageManifest:
    return PackageManifest(
        package_id,
        "rc1-publisher",
        package_id,
        "",
        PackageVersion(1),
        PackageCategory.PLUGIN,
        compatibility=PackageCompatibility(),
        metadata=PackageMetadata(),
    )


def _publisher(tier: PublisherTier = PublisherTier.VERIFIED) -> Publisher:
    return Publisher("rc1-publisher", PublisherProfile("RC-1"), tier)


def test_dependency_and_multi_root_results_install_in_deterministic_order() -> None:
    """A resolver result drives dependency-first and multi-root installation only."""
    service = ReferenceInstallerService()
    dependency_then_root = _resolved("package-a", "package-b")
    first = service.install(
        InstallationRequest(InstallationId("dependency"), dependency_then_root)
    )
    multi_root = _resolved("root-a", "root-b")
    second = service.install(
        InstallationRequest(InstallationId("multi-root"), multi_root)
    )

    assert [item.coordinate.package_id for item in first.installed] == [
        "package-a",
        "package-b",
    ]
    assert [item.coordinate.package_id for item in second.installed] == [
        "root-a",
        "root-b",
    ]


def test_publication_trust_registry_and_resolver_failure_paths_are_isolated() -> None:
    """A local rejection never changes separate reference services or snapshots."""
    rejected_publication = ReferencePublicationService(
        _publisher(PublisherTier.COMMUNITY),
        policy=PublicationPolicy(allow_community_submission=False),
    )
    rejected_publication.submit(
        PublicationRequest(PublicationId("rejected"), "rc1-publisher", _manifest("bad"))
    )
    assert rejected_publication.validate("rejected").decision.value == "reject"
    assert rejected_publication.reject("rejected").status is PublicationStatus.REJECTED

    trust = ReferenceTrustService(TrustPolicy(minimum=TrustLevel.VERIFIED))
    assert trust.evaluate(TrustLevel.COMMUNITY).decision is TrustDecision.REVIEW

    publisher = _publisher()
    publication = ReferencePublicationService(publisher)
    publication.submit(
        PublicationRequest(
            PublicationId("accepted"), "rc1-publisher", _manifest("good")
        )
    )
    publication.validate("accepted")
    accepted = publication.accept("accepted")
    registry = ReferenceRegistryService()
    adapter = ReferenceRegistryPublicationAdapter(publisher)
    registry.register_publication(RegistryEntryId("good"), accepted, adapter)
    with pytest.raises(RegistryConflictError):
        registry.register_publication(RegistryEntryId("good"), accepted, adapter)
    unresolved = ReferenceResolverService().resolve(
        ResolutionRequest(
            registry.snapshot(),
            root_requirements=(DependencyRequirement("missing"),),
        )
    )
    assert unresolved.status is ResolutionStatus.UNRESOLVED
    assert [entry.entry_id.value for entry in registry.snapshot().entries] == ["good"]


def test_installer_abort_rollback_lifecycle_and_snapshot_consistency() -> None:
    """Aborts roll back local additions; later sessions and snapshots remain stable."""

    class FailingStore(ReferenceInstallationStore):
        def __init__(self) -> None:
            super().__init__()
            self._calls = 0

        def add(self, item):
            self._calls += 1
            if self._calls == 2:
                raise RuntimeError("reference failure")
            super().add(item)

    service = ReferenceInstallerService(FailingStore())
    with pytest.raises(RuntimeError, match="reference failure"):
        service.install(
            InstallationRequest(InstallationId("abort"), _resolved("a", "b"))
        )
    aborted = service.snapshot()
    assert not aborted.installed_records
    assert aborted.transactions[0].state.value == "aborted"

    successful = service.install(
        InstallationRequest(InstallationId("success"), _resolved("c"))
    )
    before_rollback = service.snapshot()
    assert successful.session.status is InstallationStatus.SUCCEEDED
    assert service.rollback("success").state.value == "completed"
    after_rollback = service.snapshot()
    assert before_rollback.installed_records
    assert not after_rollback.installed_records
    assert after_rollback.sessions[-1].status is InstallationStatus.ROLLED_BACK

    service.close()
    service.close()
    with pytest.raises(InstallerClosedError):
        service.install(InstallationRequest(InstallationId("closed"), _resolved("d")))


def test_verification_snapshots_and_reference_services_are_immutable() -> None:
    """Snapshots are tuples and later calls do not mutate prior views."""
    publisher = _publisher()
    publication = ReferencePublicationService(publisher)
    publication.submit(
        PublicationRequest(
            PublicationId("verify"), "rc1-publisher", _manifest("verify")
        )
    )
    publication.validate("verify")
    accepted = publication.accept("verify")
    verification = ReferenceVerificationService()
    verification.verify(VerificationRequest(accepted))
    trust = ReferenceTrustService()
    trust.evaluate(TrustLevel.VERIFIED)
    publication_snapshot = publication.snapshot()
    verification_snapshot = verification.snapshot()
    trust_snapshot = trust.snapshot()

    assert isinstance(publication_snapshot, tuple)
    assert isinstance(verification_snapshot.reports, tuple)
    assert isinstance(trust_snapshot.reports, tuple)
    with pytest.raises(AttributeError):
        publication_snapshot.append(accepted)  # type: ignore[attr-defined]


def test_reference_resolver_is_thread_safe_and_instances_are_isolated() -> None:
    """Bounded concurrent reads are deterministic and use no shared singleton state."""
    request = ResolutionRequest(
        RegistrySnapshot((), RegistryIndex()),
        root_requirements=(DependencyRequirement("missing"),),
    )
    first = ReferenceResolverService()
    second = ReferenceResolverService()
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: first.resolve(request), range(32)))
    assert all(result.status is ResolutionStatus.UNRESOLVED for result in results)
    assert second.resolve(request).status is ResolutionStatus.UNRESOLVED


def test_duplicate_installs_do_not_pollute_existing_session_or_store() -> None:
    """Installer conflicts are contained, preserving an earlier successful session."""
    service = ReferenceInstallerService()
    first = service.install(
        InstallationRequest(InstallationId("one"), _resolved("same"))
    )
    with pytest.raises(InstallerConflictError):
        service.install(InstallationRequest(InstallationId("two"), _resolved("same")))
    snapshot = service.snapshot()
    assert first.session == service.get("one")
    assert [record.coordinate.package_id for record in snapshot.installed_records] == [
        "same"
    ]
