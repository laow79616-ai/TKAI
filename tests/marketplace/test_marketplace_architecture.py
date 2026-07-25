"""Offline regression tests for the Marketplace architecture contracts."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from marketplace import (
    DependencyGraph,
    MarketplaceAPI,
    MarketplaceRegistry,
    PackageDependency,
    PackageDescriptor,
    PackageInstaller,
    PackageKind,
    PackageVersion,
    PlatformGateway,
    PublisherDescriptor,
    ReferenceMarketplace,
    SignatureVerifier,
)
from marketplace.errors import DependencyResolutionError, PackageConflictError


def _package(
    package_id: str,
    *,
    kind: PackageKind = PackageKind.PLUGIN,
    dependencies: tuple[PackageDependency, ...] = (),
    metadata: dict[str, str] | None = None,
) -> PackageDescriptor:
    return PackageDescriptor(
        package_id,
        package_id.title(),
        kind,
        PackageVersion(1),
        PublisherDescriptor("publisher", "Publisher"),
        dependencies=dependencies,
        metadata={"scope": "reference"} if metadata is None else metadata,
    )


def test_package_descriptor_is_immutable_json_safe_and_defensive() -> None:
    """Package metadata remains caller-owned and serialization contains no payload."""
    metadata = {"scope": "reference"}
    package = _package(
        "plugin", dependencies=(PackageDependency("tool"),), metadata=metadata
    )
    metadata["scope"] = "changed"

    assert str(PackageVersion(1, 2, 3, "rc1")) == "1.2.3-rc1"
    assert package.to_dict()["dependencies"] == ["tool"]
    with pytest.raises(FrozenInstanceError):
        package.name = "Other"
    with pytest.raises(TypeError):
        package.metadata["scope"] = "changed"


def test_registry_and_catalog_are_stable_and_thread_safe() -> None:
    """Registry writes and snapshots are bounded, local, and stable."""
    registry = MarketplaceRegistry()
    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: registry.register(_package(str(index))), range(8)
            )
        )

    assert [package.package_id for package in registry.list()] == [
        str(index) for index in range(8)
    ]
    with pytest.raises(PackageConflictError):
        registry.register(_package("0"))
    registry.clear()
    registry.clear()
    assert registry.snapshot() == ()


def test_dependency_graph_resolves_in_order_and_rejects_invalid_graphs() -> None:
    """Dependency traversal is pure, deterministic, and never installs packages."""
    tool = _package("tool", kind=PackageKind.TOOL)
    plugin = _package("plugin", dependencies=(PackageDependency("tool"),))
    assert [
        item.package_id for item in DependencyGraph((plugin, tool)).resolve("plugin")
    ] == [
        "tool",
        "plugin",
    ]
    cyclic = _package("cycle", dependencies=(PackageDependency("cycle"),))
    with pytest.raises(DependencyResolutionError):
        DependencyGraph((cyclic,)).resolve("cycle")
    with pytest.raises(DependencyResolutionError):
        DependencyGraph((plugin,)).resolve("plugin")


def test_reference_marketplace_is_explicit_local_and_cleanup_is_idempotent() -> None:
    """Reference publication is registry-only and has no Platform side effects."""
    marketplace = ReferenceMarketplace()
    marketplace.publish(_package("memory", kind=PackageKind.MEMORY))
    assert marketplace.packages(PackageKind.MEMORY)[0].package_id == "memory"
    assert marketplace.dependency_graph().resolve("memory")[0].package_id == "memory"
    marketplace.close()
    marketplace.close()
    assert marketplace.packages() == ()


def test_contracts_and_documentation_remain_architecture_only() -> None:
    """Future API, installer, signature, and Platform boundaries are unimplemented."""
    assert all(
        getattr(contract, "_is_protocol", False)
        for contract in (
            MarketplaceAPI,
            PackageInstaller,
            SignatureVerifier,
            PlatformGateway,
        )
    )
    document = (Path(__file__).parents[2] / "docs" / "Marketplace.md").read_text(
        encoding="utf-8"
    )
    assert "No network" in document
    assert "No package download" in document
