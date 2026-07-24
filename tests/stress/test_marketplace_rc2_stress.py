"""Bounded offline Marketplace RC-2 concurrency validation."""

from concurrent.futures import ThreadPoolExecutor

from marketplace.installer import (
    InstallationId,
    InstallationRequest,
    ReferenceInstallerService,
)
from marketplace.models import PackageVersion
from marketplace.package_catalog import (
    PackageCategory,
    PackageCompatibility,
    PackageManifest,
    PackageMetadata,
)
from marketplace.publication import (
    PublicationId,
    PublicationRequest,
    ReferencePublicationService,
)
from marketplace.publisher import Publisher, PublisherProfile, PublisherRegistry
from marketplace.registry_foundation import (
    ReferenceRegistryPublicationAdapter,
    ReferenceRegistryService,
    RegistryEntryId,
    RegistrySnapshot,
)
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
    TrustLevel,
    VerificationRequest,
)


def _resolution(index: int) -> ResolutionResult:
    coordinate = DependencyCoordinate("stress", f"package-{index}", PackageVersion(1))
    return ResolutionResult(
        ResolutionStatus.RESOLVED,
        (),
        (coordinate,),
        (coordinate,),
        DependencyGraph(),
    )


def test_marketplace_reference_registries_and_services_are_bounded_under_load() -> None:
    """Eight workers perform 32 independent local Publisher/Installer operations."""
    registry = PublisherRegistry()

    def operation(index: int) -> str:
        publisher = Publisher(
            f"publisher-{index}", PublisherProfile(f"Publisher {index}")
        )
        registry.register(publisher)
        verification = ReferenceVerificationService()
        verification.verify(VerificationRequest(publisher))
        trust = ReferenceTrustService()
        trust.evaluate(TrustLevel.VERIFIED)
        installer = ReferenceInstallerService()
        result = installer.install(
            InstallationRequest(InstallationId(f"install-{index}"), _resolution(index))
        )
        return result.session.status.value

    with ThreadPoolExecutor(max_workers=8) as executor:
        statuses = list(executor.map(operation, range(32)))
    assert statuses == ["succeeded"] * 32
    assert len(registry.snapshot()) == 32


def test_marketplace_resolver_reads_are_deterministic_for_128_operations() -> None:
    """A shared resolver handles bounded concurrent reads without state corruption."""
    resolver = ReferenceResolverService()
    request = ResolutionRequest(
        RegistrySnapshot((), RegistryIndex()),
        root_requirements=(DependencyRequirement("missing"),),
    )
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(lambda _: resolver.resolve(request), range(128)))
    assert all(result.status is ResolutionStatus.UNRESOLVED for result in results)
    assert resolver.snapshot().result == results[-1]


def test_publication_and_registry_reference_chain_handles_64_operations() -> None:
    """Publication validation and Registry registration use their own local locks."""
    publisher = Publisher("shared", PublisherProfile("Shared"))
    publication = ReferencePublicationService(publisher)
    registry = ReferenceRegistryService()
    adapter = ReferenceRegistryPublicationAdapter(publisher)

    def operation(index: int) -> str:
        package_id = f"package-{index}"
        manifest = PackageManifest(
            package_id,
            "shared",
            package_id,
            "",
            PackageVersion(1),
            PackageCategory.PLUGIN,
            compatibility=PackageCompatibility(),
            metadata=PackageMetadata(),
        )
        publication_id = PublicationId(f"publication-{index}")
        publication.submit(PublicationRequest(publication_id, "shared", manifest))
        publication.validate(publication_id)
        accepted = publication.accept(publication_id)
        return registry.register_publication(
            RegistryEntryId(f"entry-{index}"), accepted, adapter
        ).entry_id.value

    with ThreadPoolExecutor(max_workers=8) as executor:
        registered = list(executor.map(operation, range(64)))
    assert len(set(registered)) == 64
    assert len(publication.snapshot()) == 64
    assert len(registry.snapshot().entries) == 64
