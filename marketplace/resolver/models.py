"""Immutable, deterministic models for local Marketplace dependency resolution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from ..models import MarketplaceValue, PackageVersion


def _metadata(value: Mapping[str, MarketplaceValue]) -> Mapping[str, MarketplaceValue]:
    return MappingProxyType(dict(value))


class ResolutionStatus(str, Enum):
    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    PARTIAL = "partial"
    INVALID = "invalid"


class ResolutionStrategy(str, Enum):
    EXACT = "exact"
    HIGHEST_COMPATIBLE = "highest_compatible"
    LOWEST_COMPATIBLE = "lowest_compatible"
    DETERMINISTIC_FIRST = "deterministic_first"


class ResolutionIssueCode(str, Enum):
    MISSING_DEPENDENCY = "missing_dependency"
    CYCLE_DETECTED = "cycle_detected"
    DUPLICATE_DEPENDENCY = "duplicate_dependency"
    VERSION_CONFLICT = "version_conflict"
    INVALID_REQUIREMENT = "invalid_requirement"
    ROOT_NOT_FOUND = "root_not_found"
    COMPATIBILITY_MISMATCH = "compatibility_mismatch"
    AMBIGUOUS_CANDIDATE = "ambiguous_candidate"
    INVALID_REGISTRY_ENTRY = "invalid_registry_entry"


@dataclass(frozen=True, slots=True)
class DependencyCoordinate:
    publisher_id: str
    package_id: str
    version: PackageVersion

    def __post_init__(self) -> None:
        if not self.publisher_id or not self.package_id:
            raise ValueError(
                "Dependency coordinate publisher and package ids are required."
            )

    def key(self) -> tuple[str, str, int, int, int, str]:
        return (
            self.publisher_id,
            self.package_id,
            self.version.major,
            self.version.minor,
            self.version.patch,
            self.version.prerelease or "",
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "publisher_id": self.publisher_id,
            "package_id": self.package_id,
            "version": str(self.version),
        }


@dataclass(frozen=True, slots=True)
class DependencyRequirement:
    package_id: str
    publisher_id: str | None = None
    version_requirement: str | None = None
    optional: bool = False
    prerelease_allowed: bool = False
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.package_id:
            raise ValueError("Dependency requirement package id is required.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def key(self) -> tuple[str, str, str, bool]:
        return (
            self.publisher_id or "",
            self.package_id,
            self.version_requirement or "",
            self.optional,
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "publisher_id": self.publisher_id,
            "package_id": self.package_id,
            "version_requirement": self.version_requirement,
            "optional": self.optional,
            "prerelease_allowed": self.prerelease_allowed,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class DependencyNode:
    coordinate: DependencyCoordinate
    dependencies: tuple[DependencyRequirement, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "dependencies", tuple(self.dependencies))


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    source: DependencyCoordinate
    target: DependencyCoordinate
    requirement: DependencyRequirement

    def key(
        self,
    ) -> tuple[
        tuple[str, str, int, int, int, str], tuple[str, str, int, int, int, str]
    ]:
        return (self.source.key(), self.target.key())


@dataclass(frozen=True, slots=True)
class DependencyGraph:
    nodes: tuple[DependencyNode, ...] = ()
    edges: tuple[DependencyEdge, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "nodes",
            tuple(sorted(self.nodes, key=lambda item: item.coordinate.key())),
        )
        object.__setattr__(
            self, "edges", tuple(sorted(self.edges, key=lambda item: item.key()))
        )

    def dependencies_of(
        self, coordinate: DependencyCoordinate
    ) -> tuple[DependencyCoordinate, ...]:
        return tuple(edge.target for edge in self.edges if edge.source == coordinate)

    def dependents_of(
        self, coordinate: DependencyCoordinate
    ) -> tuple[DependencyCoordinate, ...]:
        return tuple(edge.source for edge in self.edges if edge.target == coordinate)

    def roots(self) -> tuple[DependencyCoordinate, ...]:
        targets = {edge.target for edge in self.edges}
        return tuple(
            node.coordinate for node in self.nodes if node.coordinate not in targets
        )

    def leaves(self) -> tuple[DependencyCoordinate, ...]:
        sources = {edge.source for edge in self.edges}
        return tuple(
            node.coordinate for node in self.nodes if node.coordinate not in sources
        )

    def cycles(self) -> tuple[tuple[DependencyCoordinate, ...], ...]:
        found: list[tuple[DependencyCoordinate, ...]] = []
        visiting: list[DependencyCoordinate] = []
        visited: set[DependencyCoordinate] = set()

        def visit(node: DependencyCoordinate) -> None:
            if node in visiting:
                start = visiting.index(node)
                cycle = tuple(visiting[start:] + [node])
                if cycle not in found:
                    found.append(cycle)
                return
            if node in visited:
                return
            visiting.append(node)
            for dependency in self.dependencies_of(node):
                visit(dependency)
            visiting.pop()
            visited.add(node)

        for node in (item.coordinate for item in self.nodes):
            visit(node)
        return tuple(found)

    def topological_order(self) -> tuple[DependencyCoordinate, ...]:
        ordered: list[DependencyCoordinate] = []
        seen: set[DependencyCoordinate] = set()

        def visit(node: DependencyCoordinate) -> None:
            if node in seen:
                return
            seen.add(node)
            for dependency in self.dependencies_of(node):
                visit(dependency)
            ordered.append(node)

        for node in (item.coordinate for item in self.nodes):
            visit(node)
        return tuple(ordered)

    def snapshot(self) -> DependencyGraph:
        return self


@dataclass(frozen=True, slots=True)
class ResolutionIssue:
    code: ResolutionIssueCode
    message: str
    coordinate: DependencyCoordinate | None = None
    dependency: DependencyRequirement | None = None
    path: tuple[DependencyCoordinate, ...] = ()
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", tuple(self.path))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def key(self) -> tuple[str, str, str]:
        return (
            self.code.value,
            self.coordinate.package_id if self.coordinate else "",
            self.message,
        )


@dataclass(frozen=True, slots=True)
class ResolutionExplanation:
    code: str
    message: str
    coordinate: DependencyCoordinate | None = None
    dependency: DependencyRequirement | None = None


@dataclass(frozen=True, slots=True)
class ResolutionRequest:
    registry_snapshot: object
    root_coordinates: tuple[DependencyCoordinate, ...] = ()
    root_requirements: tuple[DependencyRequirement, ...] = ()
    strategy: ResolutionStrategy = ResolutionStrategy.DETERMINISTIC_FIRST
    target_versions: Mapping[str, str] = field(default_factory=dict)
    include_optional: bool = False
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "root_coordinates", tuple(self.root_coordinates))
        object.__setattr__(self, "root_requirements", tuple(self.root_requirements))
        object.__setattr__(self, "target_versions", _metadata(self.target_versions))
        object.__setattr__(self, "metadata", _metadata(self.metadata))
        if not self.root_coordinates and not self.root_requirements:
            raise ValueError("Resolution request requires at least one root.")
        if self.root_coordinates and self.root_requirements:
            raise ValueError(
                "Resolution request must use coordinates or requirements, not both."
            )


@dataclass(frozen=True, slots=True)
class ResolutionResult:
    status: ResolutionStatus
    requested_roots: tuple[DependencyRequirement, ...]
    selected_coordinates: tuple[DependencyCoordinate, ...]
    dependency_order: tuple[DependencyCoordinate, ...]
    graph: DependencyGraph
    issues: tuple[ResolutionIssue, ...] = ()
    explanations: tuple[ResolutionExplanation, ...] = ()
    metadata: Mapping[str, MarketplaceValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "requested_roots", tuple(self.requested_roots))
        object.__setattr__(
            self, "selected_coordinates", tuple(self.selected_coordinates)
        )
        object.__setattr__(self, "dependency_order", tuple(self.dependency_order))
        object.__setattr__(
            self, "issues", tuple(sorted(self.issues, key=lambda item: item.key()))
        )
        object.__setattr__(self, "explanations", tuple(self.explanations))
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "requested_roots": [item.to_dict() for item in self.requested_roots],
            "selected_coordinates": [
                item.to_dict() for item in self.selected_coordinates
            ],
            "dependency_order": [item.to_dict() for item in self.dependency_order],
            "issues": [
                {"code": item.code.value, "message": item.message}
                for item in self.issues
            ],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ResolutionSnapshot:
    result: ResolutionResult | None = None
