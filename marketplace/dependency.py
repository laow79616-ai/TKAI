"""Pure, deterministic dependency graph for Marketplace descriptor validation."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import DependencyResolutionError
from .models import PackageDescriptor


class DependencyGraph:
    """Resolve declarative package ordering without downloading or installing."""

    def __init__(self, packages: Iterable[PackageDescriptor]) -> None:
        descriptors = tuple(packages)
        self._packages = {package.package_id: package for package in descriptors}
        if len(self._packages) != len(descriptors):
            raise ValueError("Dependency graph package ids must be unique.")

    def dependencies_for(self, package_id: str) -> tuple[str, ...]:
        """Return declared dependency identifiers in source order."""
        try:
            package = self._packages[package_id]
        except KeyError as exc:
            raise DependencyResolutionError(package_id) from exc
        return tuple(dependency.package_id for dependency in package.dependencies)

    def resolve(self, package_id: str) -> tuple[PackageDescriptor, ...]:
        """Return dependencies-first order or raise for missing/cyclic declarations."""
        ordered: list[PackageDescriptor] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(identifier: str) -> None:
            if identifier in visited:
                return
            if identifier in visiting:
                raise DependencyResolutionError(f"Cyclic dependency at {identifier}.")
            try:
                package = self._packages[identifier]
            except KeyError as exc:
                raise DependencyResolutionError(
                    f"Missing dependency {identifier}."
                ) from exc
            visiting.add(identifier)
            for dependency in package.dependencies:
                if dependency.required:
                    visit(dependency.package_id)
            visiting.remove(identifier)
            visited.add(identifier)
            ordered.append(package)

        visit(package_id)
        return tuple(ordered)
