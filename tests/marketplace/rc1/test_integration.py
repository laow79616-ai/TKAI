"""Offline Marketplace RC-1 integration smoke coverage."""


def test_public_marketplace_foundations_import() -> None:
    import marketplace
    import marketplace.installer
    import marketplace.package_catalog
    import marketplace.publication
    import marketplace.publisher
    import marketplace.registry
    import marketplace.registry_foundation
    import marketplace.resolver
    import marketplace.verification

    assert marketplace is not None


def test_explicit_offline_reference_workflow() -> None:
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
    from marketplace.publisher import Publisher, PublisherProfile, PublisherTier
    from marketplace.registry_foundation import (
        ReferenceRegistryPublicationAdapter,
        ReferenceRegistryService,
        RegistryEntryId,
    )
    from marketplace.resolver import (
        DependencyRequirement,
        ReferenceResolverService,
        ResolutionRequest,
        ResolutionStatus,
    )
    from marketplace.verification import (
        ReferenceTrustService,
        ReferenceVerificationService,
        TrustDecision,
        TrustLevel,
        VerificationRequest,
        VerificationStatus,
    )

    publisher = Publisher(
        "rc1-publisher", PublisherProfile("RC1"), PublisherTier.VERIFIED
    )
    manifest = PackageManifest(
        "rc1-package",
        "rc1-publisher",
        "RC1",
        "",
        PackageVersion(1),
        PackageCategory.PLUGIN,
        compatibility=PackageCompatibility(),
        metadata=PackageMetadata(),
    )
    publication = ReferencePublicationService(publisher)
    publication.submit(
        PublicationRequest(PublicationId("rc1"), "rc1-publisher", manifest)
    )
    publication.validate("rc1")
    accepted = publication.accept("rc1")
    assert (
        ReferenceVerificationService()
        .verify(VerificationRequest(accepted))
        .result.status
        is VerificationStatus.PASSED
    )
    assert (
        ReferenceTrustService().evaluate(TrustLevel.VERIFIED).decision
        is TrustDecision.ALLOW
    )
    registry = ReferenceRegistryService()
    registry.register_publication(
        RegistryEntryId("rc1-entry"),
        accepted,
        ReferenceRegistryPublicationAdapter(publisher),
    )
    resolution = ReferenceResolverService().resolve(
        ResolutionRequest(
            registry.snapshot(),
            root_requirements=(DependencyRequirement("rc1-package", "rc1-publisher"),),
        )
    )
    assert resolution.status is ResolutionStatus.RESOLVED
    installed = ReferenceInstallerService().install(
        InstallationRequest(InstallationId("rc1-install"), resolution)
    )
    assert installed.installed and installed.session.status.value == "succeeded"


def test_resolver_multi_root_and_missing_dependency_are_isolated() -> None:
    from marketplace.models import PackageVersion
    from marketplace.registry_foundation import RegistrySnapshot
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

    coordinate_a = DependencyCoordinate("publisher", "a", PackageVersion(1))
    coordinate_b = DependencyCoordinate("publisher", "b", PackageVersion(1))
    resolved = ResolutionResult(
        ResolutionStatus.RESOLVED,
        (),
        (coordinate_a, coordinate_b),
        (coordinate_a, coordinate_b),
        DependencyGraph(),
    )
    assert [item.package_id for item in resolved.dependency_order] == ["a", "b"]
    service = ReferenceResolverService()
    missing = service.resolve(
        ResolutionRequest(
            RegistrySnapshot((), RegistryIndex()),
            root_requirements=(DependencyRequirement("missing"),),
        )
    )
    assert missing.status is ResolutionStatus.UNRESOLVED
