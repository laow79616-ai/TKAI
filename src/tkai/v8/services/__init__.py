"""Reference-only discovery, graph, health, and diagnostics services."""

from __future__ import annotations

from collections.abc import Iterable

from tkai.v8.contracts import Diagnostic, HealthStatus, RegistryRecord, Scope
from tkai.v8.registry import MetadataRegistry, RegistryCatalog


class DiscoveryService:
    """Discovers metadata without importing or calling providers."""

    def __init__(self, registries: RegistryCatalog) -> None:
        self._registries = registries

    def frameworks(self, scope: Scope | None = None) -> tuple[RegistryRecord, ...]:
        return self._registries.frameworks.discover(scope=scope)

    def services(self, scope: Scope | None = None) -> tuple[RegistryRecord, ...]:
        return self._registries.modules.discover(scope=scope, kind="service")

    def capabilities(self, scope: Scope | None = None) -> tuple[RegistryRecord, ...]:
        return self._registries.capabilities.discover(scope=scope)


class DependencyGraph:
    """Validates and renders registry dependency references."""

    def __init__(self, registries: Iterable[MetadataRegistry]) -> None:
        records = [record for registry in registries for record in registry.discover()]
        self._records = {record.identifier: record for record in records}

    def as_dict(self) -> dict[str, tuple[str, ...]]:
        return {
            identifier: tuple(item.target for item in record.dependencies)
            for identifier, record in sorted(self._records.items())
        }

    def resolve(self, identifier: str) -> tuple[str, ...]:
        visiting: set[str] = set()
        visited: set[str] = set()
        ordered: list[str] = []

        def visit(current: str) -> None:
            if current in visiting:
                raise ValueError(f"dependency cycle at {current}")
            if current in visited:
                return
            if current not in self._records:
                raise LookupError(current)
            visiting.add(current)
            for dependency in self._records[current].dependencies:
                if dependency.target not in self._records:
                    if dependency.optional:
                        continue
                    raise LookupError(dependency.target)
                visit(dependency.target)
            visiting.remove(current)
            visited.add(current)
            ordered.append(current)

        visit(identifier)
        return tuple(ordered)


class HealthAggregator:
    """Aggregates published health metadata without probing providers."""

    def aggregate(self, registries: Iterable[MetadataRegistry]) -> dict[str, object]:
        records = [record for registry in registries for record in registry.discover()]
        counts = {status.value: 0 for status in HealthStatus}
        for record in records:
            counts[record.health.value] += 1
        status = HealthStatus.HEALTHY
        if counts[HealthStatus.UNHEALTHY.value]:
            status = HealthStatus.UNHEALTHY
        elif counts[HealthStatus.DEGRADED.value]:
            status = HealthStatus.DEGRADED
        elif records and counts[HealthStatus.UNKNOWN.value] == len(records):
            status = HealthStatus.UNKNOWN
        return {"status": status.value, "counts": counts, "total": len(records)}


class DiagnosticsAggregator:
    """Aggregates structured diagnostics and missing dependency metadata."""

    def aggregate(
        self,
        registries: Iterable[MetadataRegistry],
        diagnostics: Iterable[Diagnostic],
    ) -> tuple[Diagnostic, ...]:
        records = [record for registry in registries for record in registry.discover()]
        identifiers = {record.identifier for record in records}
        results = list(diagnostics)
        for record in records:
            for dependency in record.dependencies:
                if dependency.target not in identifiers and not dependency.optional:
                    results.append(
                        Diagnostic(
                            code="missing-dependency",
                            message=(
                                f"{record.identifier} references missing "
                                f"{dependency.target}"
                            ),
                            severity="error",
                            source=record.identifier,
                            scope=record.scope,
                        )
                    )
        return tuple(results)


__all__ = (
    "DependencyGraph",
    "DiagnosticsAggregator",
    "DiscoveryService",
    "HealthAggregator",
)
