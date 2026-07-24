"""Offline deterministic reference dependency resolver with no package mutation."""

from __future__ import annotations

from threading import RLock

from ..models import PackageDependency, PackageVersion
from ..registry_foundation import RegistryEntry, RegistrySnapshot
from .errors import ResolverClosedError
from .graph import DependencyGraphBuilder
from .models import (
    DependencyCoordinate,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyRequirement,
    ResolutionExplanation,
    ResolutionIssue,
    ResolutionIssueCode,
    ResolutionRequest,
    ResolutionResult,
    ResolutionSnapshot,
    ResolutionStatus,
    ResolutionStrategy,
)
from .source import ReferenceRegistryResolutionSource, RegistryResolutionSource


class ReferenceResolverService:
    """Resolve one explicit local snapshot at a time and retain only its last result."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._last = ResolutionSnapshot()
        self._closed = False

    def resolve(self, request: ResolutionRequest) -> ResolutionResult:
        """Build a local graph and result without querying or mutating any service."""
        with self._lock:
            self._ensure_open()
            result = self._resolve(request)
            self._last = ResolutionSnapshot(result)
            return result

    def validate(self, request: ResolutionRequest) -> tuple[ResolutionIssue, ...]:
        """Return deterministic issues from a normal local resolution pass."""
        return self.resolve(request).issues

    def explain(
        self, result: ResolutionResult | None = None
    ) -> tuple[ResolutionExplanation, ...]:
        """Return stable explanations for an explicit or last local result."""
        with self._lock:
            self._ensure_open()
            selected = self._last.result if result is None else result
            return () if selected is None else selected.explanations

    def build_graph(self, request: ResolutionRequest) -> DependencyGraph:
        """Return the graph from an isolated resolution pass."""
        return self.resolve(request).graph

    def snapshot(self) -> ResolutionSnapshot:
        """Return the last immutable descriptive result only."""
        with self._lock:
            self._ensure_open()
            return self._last

    def clear(self) -> None:
        """Clear the bounded last-result snapshot without affecting other services."""
        with self._lock:
            self._ensure_open()
            self._last = ResolutionSnapshot()

    def close(self) -> None:
        """Idempotently release the bounded local state."""
        with self._lock:
            if self._closed:
                return
            self._last = ResolutionSnapshot()
            self._closed = True

    def _resolve(self, request: ResolutionRequest) -> ResolutionResult:
        source = self._source(request.registry_snapshot)
        candidates = source.candidates()
        builder = DependencyGraphBuilder()
        selected: dict[DependencyCoordinate, RegistryEntry] = {}
        issues: list[ResolutionIssue] = []
        explanations: list[ResolutionExplanation] = []
        requested = self._roots(request)
        visiting: list[DependencyCoordinate] = []
        requirements: dict[tuple[str | None, str], set[str]] = {}

        def choose(requirement: DependencyRequirement) -> RegistryEntry | None:
            matches = [
                entry
                for entry in candidates
                if entry.package_manifest.package_id == requirement.package_id
                and (
                    requirement.publisher_id is None
                    or entry.publisher.publisher_id == requirement.publisher_id
                )
                and self._matches_version(entry.package_manifest.version, requirement)
            ]
            if not matches:
                return None
            matches.sort(key=lambda entry: self._coordinate(entry).key())
            if len(matches) > 1:
                issues.append(
                    ResolutionIssue(
                        ResolutionIssueCode.AMBIGUOUS_CANDIDATE,
                        "Multiple local candidates match dependency; "
                        "deterministic selection used.",
                        dependency=requirement,
                    )
                )
            if request.strategy is ResolutionStrategy.HIGHEST_COMPATIBLE:
                return max(
                    matches,
                    key=lambda entry: self._version_key(entry.package_manifest.version),
                )
            if request.strategy is ResolutionStrategy.LOWEST_COMPATIBLE:
                return min(
                    matches,
                    key=lambda entry: self._version_key(entry.package_manifest.version),
                )
            return matches[0]

        def expand(
            requirement: DependencyRequirement,
            parent: DependencyCoordinate | None = None,
        ) -> DependencyCoordinate | None:
            key = (requirement.publisher_id, requirement.package_id)
            version_text = requirement.version_requirement or "any"
            previous = requirements.setdefault(key, set())
            previous.add(version_text)
            if len(previous) > 1 and all(item != "any" for item in previous):
                issues.append(
                    ResolutionIssue(
                        ResolutionIssueCode.VERSION_CONFLICT,
                        "Conflicting local dependency version requirements.",
                        dependency=requirement,
                    )
                )
            entry = choose(requirement)
            if entry is None:
                if not requirement.optional or request.include_optional:
                    code = (
                        ResolutionIssueCode.ROOT_NOT_FOUND
                        if parent is None
                        else ResolutionIssueCode.MISSING_DEPENDENCY
                    )
                    issues.append(
                        ResolutionIssue(
                            code,
                            "No local registry candidate satisfies dependency.",
                            dependency=requirement,
                            path=tuple(visiting),
                        )
                    )
                else:
                    explanations.append(
                        ResolutionExplanation(
                            "optional_dependency_skipped",
                            "Optional dependency has no local candidate "
                            "and was skipped.",
                            dependency=requirement,
                        )
                    )
                return None
            coordinate = self._coordinate(entry)
            if coordinate in selected:
                if parent is not None:
                    builder.add_edge(DependencyEdge(parent, coordinate, requirement))
                return coordinate
            selected[coordinate] = entry
            builder.add_node(
                DependencyNode(coordinate, self._requirements(entry.dependencies))
            )
            if parent is not None:
                builder.add_edge(DependencyEdge(parent, coordinate, requirement))
            for layer, target_version in request.target_versions.items():
                declared = getattr(entry.compatibility, layer, None)
                if declared is not None and declared != target_version:
                    issues.append(
                        ResolutionIssue(
                            ResolutionIssueCode.COMPATIBILITY_MISMATCH,
                            "Explicit target version does not match "
                            "compatibility declaration.",
                            coordinate=coordinate,
                            metadata={"layer": layer, "target": target_version},
                        )
                    )
            visiting.append(coordinate)
            seen_requirements: set[tuple[str, str | None, str | None]] = set()
            for dependency in self._requirements(entry.dependencies):
                duplicate_key = (
                    dependency.package_id,
                    dependency.publisher_id,
                    dependency.version_requirement,
                )
                if duplicate_key in seen_requirements:
                    issues.append(
                        ResolutionIssue(
                            ResolutionIssueCode.DUPLICATE_DEPENDENCY,
                            "Duplicate dependency declaration.",
                            coordinate=coordinate,
                            dependency=dependency,
                        )
                    )
                    continue
                seen_requirements.add(duplicate_key)
                target = expand(dependency, coordinate)
                if target is not None and target in visiting:
                    path = tuple(visiting[visiting.index(target) :] + [target])
                    issues.append(
                        ResolutionIssue(
                            ResolutionIssueCode.CYCLE_DETECTED,
                            "Dependency cycle detected.",
                            coordinate=coordinate,
                            dependency=dependency,
                            path=path,
                        )
                    )
                    explanations.append(
                        ResolutionExplanation(
                            "cycle_detected",
                            "A local dependency cycle was detected.",
                            coordinate=coordinate,
                            dependency=dependency,
                        )
                    )
            visiting.pop()
            explanations.append(
                ResolutionExplanation(
                    "candidate_selected",
                    "Candidate selected using deterministic local ordering.",
                    coordinate=coordinate,
                    dependency=requirement,
                )
            )
            return coordinate

        for root in requested:
            expand(root)
        graph = builder.build()
        cycle_paths = graph.cycles()
        for cycle in cycle_paths:
            issue = ResolutionIssue(
                ResolutionIssueCode.CYCLE_DETECTED,
                "Dependency cycle detected.",
                path=cycle,
            )
            if issue not in issues:
                issues.append(issue)
        ordered = (
            graph.topological_order()
            if not any(
                issue.code is ResolutionIssueCode.CYCLE_DETECTED for issue in issues
            )
            else ()
        )
        fatal = [
            issue
            for issue in issues
            if issue.code is not ResolutionIssueCode.AMBIGUOUS_CANDIDATE
        ]
        status = (
            ResolutionStatus.RESOLVED
            if not fatal
            else (ResolutionStatus.PARTIAL if selected else ResolutionStatus.UNRESOLVED)
        )
        return ResolutionResult(
            status,
            tuple(requested),
            tuple(sorted(selected, key=lambda item: item.key())),
            ordered,
            graph,
            tuple(issues),
            tuple(explanations),
            request.metadata,
        )

    @staticmethod
    def _source(snapshot: object) -> RegistryResolutionSource:
        if isinstance(snapshot, ReferenceRegistryResolutionSource):
            return snapshot
        if not isinstance(snapshot, RegistrySnapshot):
            raise TypeError("Resolution request requires a RegistrySnapshot.")
        return ReferenceRegistryResolutionSource(snapshot)

    @staticmethod
    def _roots(request: ResolutionRequest) -> tuple[DependencyRequirement, ...]:
        if request.root_requirements:
            return request.root_requirements
        return tuple(
            DependencyRequirement(
                item.package_id, item.publisher_id, f"=={item.version}"
            )
            for item in request.root_coordinates
        )

    @staticmethod
    def _coordinate(entry: RegistryEntry) -> DependencyCoordinate:
        return DependencyCoordinate(
            entry.coordinate.publisher_id,
            entry.coordinate.package_id,
            entry.coordinate.version,
        )

    @staticmethod
    def _requirements(
        dependencies: tuple[PackageDependency, ...],
    ) -> tuple[DependencyRequirement, ...]:
        return tuple(
            DependencyRequirement(
                item.package_id,
                version_requirement=item.version_constraint,
                optional=not item.required,
            )
            for item in dependencies
        )

    @staticmethod
    def _version_key(version: PackageVersion) -> tuple[int, int, int, str]:
        return (version.major, version.minor, version.patch, version.prerelease or "")

    def _matches_version(
        self, version: PackageVersion, requirement: DependencyRequirement
    ) -> bool:
        text = requirement.version_requirement
        if version.prerelease is not None and not requirement.prerelease_allowed:
            return False
        if text is None or text == "" or text == "any":
            return True
        if text.startswith("=="):
            return str(version) == text[2:]
        if text.startswith(">=") and ",<" in text:
            lower, upper = text.split(",<", maxsplit=1)
            return self._version_key(version) >= self._parse_version(
                lower[2:]
            ) and self._version_key(version) < self._parse_version(upper)
        return False

    @staticmethod
    def _parse_version(value: str) -> tuple[int, int, int, str]:
        main, separator, prerelease = value.partition("-")
        parts = main.split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):
            return (10**9, 10**9, 10**9, "invalid")
        return (
            int(parts[0]),
            int(parts[1]),
            int(parts[2]),
            prerelease if separator else "",
        )

    def _ensure_open(self) -> None:
        if self._closed:
            raise ResolverClosedError("Resolver service is closed.")
