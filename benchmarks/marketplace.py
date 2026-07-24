"""Bounded offline Marketplace RC-2 benchmark scenarios.

The module measures reference-only operations and deliberately makes no
performance promise.  Every operation creates or reads local immutable state.
"""

from __future__ import annotations

from collections.abc import Callable

from marketplace.installer import (
    InstallationId,
    InstallationRequest,
    ReferenceInstallerService,
)
from marketplace.installer.errors import InstallerConflictError
from marketplace.models import PackageDependency, PackageVersion
from marketplace.package_catalog import (
    PackageCategory,
    PackageCompatibility,
    PackageManifest,
    PackageMetadata,
)
from marketplace.publisher import Publisher, PublisherProfile
from marketplace.registry_foundation import (
    RegistryCoordinate,
    RegistryEntry,
    RegistryEntryId,
    RegistrySnapshot,
    RegistryStatus,
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
    ReferenceVerificationService,
    VerificationLevel,
    VerificationRequest,
)

from .base import BenchmarkRunner
from .models import BenchmarkResult
from .report import BenchmarkReport


def _runner(iterations: int) -> BenchmarkRunner:
    return BenchmarkRunner(warmup=1, iterations=iterations, random_seed=5_002)


def _entry(
    package_id: str, dependencies: tuple[PackageDependency, ...] = ()
) -> RegistryEntry:
    publisher = Publisher("benchmark", PublisherProfile("Benchmark"))
    manifest = PackageManifest(
        package_id,
        "benchmark",
        package_id,
        "",
        PackageVersion(1),
        PackageCategory.PLUGIN,
        dependencies=dependencies,
        compatibility=PackageCompatibility(),
        metadata=PackageMetadata(),
    )
    return RegistryEntry(
        RegistryEntryId(package_id),
        RegistryCoordinate("benchmark", package_id, PackageVersion(1)),
        package_id,
        manifest,
        publisher,
        PackageCategory.PLUGIN,
        dependencies,
        manifest.compatibility,
        manifest.tags,
        RegistryStatus.ACTIVE,
    )


def _request(entries: tuple[RegistryEntry, ...], *roots: str) -> ResolutionRequest:
    return ResolutionRequest(
        RegistrySnapshot(entries, RegistryIndex()),
        root_requirements=tuple(DependencyRequirement(root) for root in roots),
    )


def _resolution(*package_ids: str) -> ResolutionResult:
    coordinates = tuple(
        DependencyCoordinate("benchmark", package_id, PackageVersion(1))
        for package_id in package_ids
    )
    return ResolutionResult(
        ResolutionStatus.RESOLVED,
        (),
        coordinates,
        coordinates,
        DependencyGraph(),
    )


def benchmark_verification_basic(iterations: int = 10) -> BenchmarkResult:
    return _runner(iterations).run(
        lambda: ReferenceVerificationService().verify(
            VerificationRequest(object(), VerificationLevel.BASIC)
        )
    )


def benchmark_verification_standard(iterations: int = 10) -> BenchmarkResult:
    return _runner(iterations).run(
        lambda: ReferenceVerificationService().verify(
            VerificationRequest(object(), VerificationLevel.STANDARD)
        )
    )


def benchmark_verification_strict(iterations: int = 10) -> BenchmarkResult:
    return _runner(iterations).run(
        lambda: ReferenceVerificationService().verify(
            VerificationRequest(object(), VerificationLevel.STRICT)
        )
    )


def benchmark_resolver_linear(iterations: int = 10) -> BenchmarkResult:
    entries = (
        _entry("base"),
        _entry("root", (PackageDependency("base"),)),
    )
    request = _request(entries, "root")
    return _runner(iterations).run(lambda: ReferenceResolverService().resolve(request))


def benchmark_resolver_branch(iterations: int = 10) -> BenchmarkResult:
    entries = (
        _entry("left"),
        _entry("right"),
        _entry("root", (PackageDependency("left"), PackageDependency("right"))),
    )
    request = _request(entries, "root")
    return _runner(iterations).run(lambda: ReferenceResolverService().resolve(request))


def benchmark_resolver_multi_root(iterations: int = 10) -> BenchmarkResult:
    request = _request((_entry("root-a"), _entry("root-b")), "root-a", "root-b")
    return _runner(iterations).run(lambda: ReferenceResolverService().resolve(request))


def benchmark_resolver_missing(iterations: int = 10) -> BenchmarkResult:
    request = _request((), "missing")
    return _runner(iterations).run(lambda: ReferenceResolverService().resolve(request))


def benchmark_resolver_cycle(iterations: int = 10) -> BenchmarkResult:
    entries = (
        _entry("a", (PackageDependency("b"),)),
        _entry("b", (PackageDependency("a"),)),
    )
    request = _request(entries, "a")
    return _runner(iterations).run(lambda: ReferenceResolverService().resolve(request))


def benchmark_installer_single(iterations: int = 10) -> BenchmarkResult:
    return _runner(iterations).run(
        lambda: ReferenceInstallerService().install(
            InstallationRequest(InstallationId("single"), _resolution("single"))
        )
    )


def benchmark_installer_dependency(iterations: int = 10) -> BenchmarkResult:
    return _runner(iterations).run(
        lambda: ReferenceInstallerService().install(
            InstallationRequest(
                InstallationId("dependency"), _resolution("base", "root")
            )
        )
    )


def benchmark_installer_transaction(iterations: int = 10) -> BenchmarkResult:
    return _runner(iterations).run(
        lambda: ReferenceInstallerService()
        .install(
            InstallationRequest(InstallationId("transaction"), _resolution("package"))
        )
        .session
    )


def benchmark_installer_rollback(iterations: int = 10) -> BenchmarkResult:
    def operation() -> object:
        service = ReferenceInstallerService()
        service.install(
            InstallationRequest(InstallationId("rollback"), _resolution("p"))
        )
        return service.rollback("rollback")

    return _runner(iterations).run(operation)


def benchmark_installer_verification(iterations: int = 10) -> BenchmarkResult:
    return benchmark_installer_single(iterations)


def benchmark_installer_duplicate(iterations: int = 10) -> BenchmarkResult:
    def operation() -> object:
        service = ReferenceInstallerService()
        request = InstallationRequest(InstallationId("duplicate"), _resolution("p"))
        service.install(request)
        try:
            return service.install(
                InstallationRequest(InstallationId("duplicate-2"), _resolution("p"))
            )
        except InstallerConflictError:
            return service.snapshot()

    return _runner(iterations).run(operation)


MARKETPLACE_BENCHMARKS: tuple[tuple[str, Callable[[int], BenchmarkResult]], ...] = (
    ("marketplace.verification.basic", benchmark_verification_basic),
    ("marketplace.verification.standard", benchmark_verification_standard),
    ("marketplace.verification.strict", benchmark_verification_strict),
    ("marketplace.resolver.linear", benchmark_resolver_linear),
    ("marketplace.resolver.branch", benchmark_resolver_branch),
    ("marketplace.resolver.multi_root", benchmark_resolver_multi_root),
    ("marketplace.resolver.missing", benchmark_resolver_missing),
    ("marketplace.resolver.cycle", benchmark_resolver_cycle),
    ("marketplace.installer.single", benchmark_installer_single),
    ("marketplace.installer.dependency", benchmark_installer_dependency),
    ("marketplace.installer.transaction", benchmark_installer_transaction),
    ("marketplace.installer.rollback", benchmark_installer_rollback),
    ("marketplace.installer.verification", benchmark_installer_verification),
    ("marketplace.installer.duplicate", benchmark_installer_duplicate),
)


def run_benchmark(iterations: int = 10) -> BenchmarkResult:
    """Provide a conventional module entry point without recording a threshold."""
    return benchmark_installer_single(iterations)


def reports(iterations: int = 10) -> dict[str, dict[str, str]]:
    """Render deterministic report shapes for every bounded scenario."""
    return {
        name: {
            "markdown": BenchmarkReport.to_markdown(name, benchmark(iterations)),
            "json": BenchmarkReport.to_json(name, benchmark(iterations)),
        }
        for name, benchmark in MARKETPLACE_BENCHMARKS
    }


if __name__ == "__main__":
    BenchmarkReport.emit("marketplace.installer.single", run_benchmark())
