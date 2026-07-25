"""Reference-only local dependency declarations and deterministic resolution."""

from __future__ import annotations

from dataclasses import dataclass

from .errors import PluginDependencyError


@dataclass(frozen=True, slots=True)
class PluginDependency:
    """One named local dependency; version resolution is deliberately deferred."""

    name: str
    version: str | None = None


def resolve_dependencies(
    name: str, dependencies: dict[str, tuple[PluginDependency, ...]]
) -> tuple[str, ...]:
    """Return deterministic dependency-first order or a clear local graph error."""
    ordered: list[str] = []
    active: set[str] = set()
    visited: set[str] = set()

    def visit(current: str) -> None:
        if current in active:
            raise PluginDependencyError(f"Cyclic plugin dependency: {current}")
        if current in visited:
            return
        if current not in dependencies:
            raise PluginDependencyError(f"Missing plugin dependency: {current}")
        active.add(current)
        for dependency in sorted(dependencies[current], key=lambda item: item.name):
            visit(dependency.name)
        active.remove(current)
        visited.add(current)
        ordered.append(current)

    visit(name)
    return tuple(ordered)
