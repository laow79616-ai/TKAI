"""Deterministic regression coverage for the offline Dependency Resolver Foundation."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

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
    DependencyGraphBuilder,
    DependencyNode,
    DependencyRequirement,
    ReferenceRegistryResolutionSource,
    ReferenceResolverService,
    ResolutionIssueCode,
    ResolutionRequest,
    ResolutionStatus,
    ResolverClosedError,
)


def _entry(
    package_id: str,
    dependencies: tuple[PackageDependency, ...] = (),
    version: PackageVersion | None = None,
) -> RegistryEntry:
    selected_version = PackageVersion(1) if version is None else version
    publisher = Publisher("publisher", PublisherProfile("Publisher"))
    manifest = PackageManifest(
        package_id,
        "publisher",
        package_id,
        "Reference",
        selected_version,
        PackageCategory.PLUGIN,
        dependencies=dependencies,
        compatibility=PackageCompatibility(runtime="1.3"),
        metadata=PackageMetadata(),
    )
    return RegistryEntry(
        RegistryEntryId(package_id),
        RegistryCoordinate("publisher", package_id, selected_version),
        f"publication-{package_id}",
        manifest,
        publisher,
        PackageCategory.PLUGIN,
        dependencies,
        manifest.compatibility,
        manifest.tags,
        RegistryStatus.ACTIVE,
    )


def _snapshot(*entries: RegistryEntry) -> RegistrySnapshot:
    return RegistrySnapshot(tuple(entries), RegistryIndex())


def _request(
    *entries: RegistryEntry, root: str = "root", **kwargs: object
) -> ResolutionRequest:
    return ResolutionRequest(
        _snapshot(*entries), root_requirements=(DependencyRequirement(root),), **kwargs
    )


def test_models_are_immutable_defensive_and_json_safe() -> None:
    metadata = {"source": "test"}
    requirement = DependencyRequirement("package", metadata=metadata)
    metadata["source"] = "changed"
    assert requirement.metadata == {"source": "test"}
    with pytest.raises(FrozenInstanceError):
        requirement.package_id = "other"
    assert (
        DependencyCoordinate("publisher", "package", PackageVersion(1)).to_dict()[
            "version"
        ]
        == "1.0.0"
    )


def test_registry_source_is_read_only_and_resolution_is_dependency_first() -> None:
    base = _entry("base")
    root = _entry("root", (PackageDependency("base"),))
    snapshot = _snapshot(root, base)
    source = ReferenceRegistryResolutionSource(snapshot)
    result = ReferenceResolverService().resolve(
        ResolutionRequest(source, root_requirements=(DependencyRequirement("root"),))
    )
    assert result.status is ResolutionStatus.RESOLVED
    assert [item.package_id for item in result.dependency_order] == ["base", "root"]
    assert source.candidates() == source.candidates()


def test_missing_optional_duplicate_and_multiple_roots_are_diagnostic() -> None:
    root = _entry(
        "root",
        (
            PackageDependency("missing"),
            PackageDependency("optional", required=False),
        ),
    )
    other = _entry("other")
    request = ResolutionRequest(
        _snapshot(root, other),
        root_requirements=(
            DependencyRequirement("root"),
            DependencyRequirement("other"),
        ),
    )
    result = ReferenceResolverService().resolve(request)
    assert result.status is ResolutionStatus.PARTIAL
    assert [issue.code for issue in result.issues] == [
        ResolutionIssueCode.MISSING_DEPENDENCY,
    ]
    assert [item.package_id for item in result.selected_coordinates] == [
        "other",
        "root",
    ]


def test_cycle_missing_root_and_graph_queries_are_deterministic() -> None:
    first = _entry("first", (PackageDependency("second"),))
    second = _entry("second", (PackageDependency("first"),))
    result = ReferenceResolverService().resolve(_request(first, second, root="first"))
    assert any(
        issue.code is ResolutionIssueCode.CYCLE_DETECTED for issue in result.issues
    )
    assert result.dependency_order == ()
    assert result.graph.cycles()[0][0].package_id == "first"
    missing = ReferenceResolverService().resolve(_request(root="missing"))
    assert missing.status is ResolutionStatus.UNRESOLVED
    assert missing.issues[0].code is ResolutionIssueCode.ROOT_NOT_FOUND


def test_exact_compatible_conflict_and_deterministic_candidate_selection() -> None:
    v1 = _entry("package", version=PackageVersion(1, 2, 0))
    v2 = _entry("package", version=PackageVersion(1, 3, 0))
    service = ReferenceResolverService()
    exact = service.resolve(
        ResolutionRequest(
            _snapshot(v2, v1),
            root_requirements=(
                DependencyRequirement("package", version_requirement="==1.2.0"),
            ),
        )
    )
    assert exact.selected_coordinates[0].version == PackageVersion(1, 2, 0)
    compatible = service.resolve(
        ResolutionRequest(
            _snapshot(v2, v1),
            root_requirements=(
                DependencyRequirement("package", version_requirement=">=1.2.0,<2.0.0"),
            ),
        )
    )
    assert compatible.selected_coordinates[0].version == PackageVersion(1, 2, 0)


def test_graph_builder_snapshot_thread_safety_and_lifecycle_are_explicit() -> None:
    coordinate = DependencyCoordinate("publisher", "one", PackageVersion(1))
    builder = DependencyGraphBuilder()
    builder.add_node(DependencyNode(coordinate))
    assert builder.build().roots() == (coordinate,)
    service = ReferenceResolverService()
    root = _entry("root")
    request = _request(root)
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _item: service.resolve(request), range(8)))
    assert all(result.status is ResolutionStatus.RESOLVED for result in results)
    service.clear()
    assert service.snapshot().result is None
    service.close()
    service.close()
    with pytest.raises(ResolverClosedError):
        service.snapshot()
