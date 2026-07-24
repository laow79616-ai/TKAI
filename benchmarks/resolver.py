"""Lightweight offline Dependency Resolver Foundation benchmarks."""

from __future__ import annotations

from .base import BenchmarkRunner
from .report import BenchmarkReport


def run() -> dict[str, object]:
    """Run a tiny local linear-resolution scenario and return stable report inputs."""
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
        DependencyRequirement,
        ReferenceResolverService,
        ResolutionRequest,
    )

    publisher = Publisher("benchmark", PublisherProfile("Benchmark"))

    def entry(
        package_id: str, dependencies: tuple[PackageDependency, ...] = ()
    ) -> RegistryEntry:
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

    base, root = entry("base"), entry("root", (PackageDependency("base"),))
    request = ResolutionRequest(
        RegistrySnapshot((root, base), RegistryIndex()),
        root_requirements=(DependencyRequirement("root"),),
    )
    result = BenchmarkRunner(iterations=5, repeats=1, random_seed=0).run(
        lambda: ReferenceResolverService().resolve(request)
    )
    return {
        "result": result,
        "markdown": BenchmarkReport.to_markdown("resolver-linear", result),
        "json": BenchmarkReport.to_json("resolver-linear", result),
    }


if __name__ == "__main__":
    output = run()
    print(output["markdown"])
