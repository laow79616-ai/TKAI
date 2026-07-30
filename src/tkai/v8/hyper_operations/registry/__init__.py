"""Typed registries for immutable operations metadata."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from tkai.v8.hyper_operations import contracts

T = TypeVar("T")


class MetadataRegistry(Generic[T]):
    def __init__(self, identifier: Callable[[T], str]) -> None:
        self._identifier = identifier
        self._records: dict[str, T] = {}

    def register(self, value: T) -> T:
        identifier = self._identifier(value)
        if identifier in self._records:
            raise ValueError(f"metadata record already registered: {identifier}")
        self._records[identifier] = value
        return value

    def get(self, identifier: str) -> T:
        return self._records[identifier]

    def discover(self) -> tuple[T, ...]:
        return tuple(self._records[key] for key in sorted(self._records))

    def __len__(self) -> int:
        return len(self._records)


class OperationsRegistryCatalog:
    profiles: MetadataRegistry[contracts.OperationProfile]
    readiness: MetadataRegistry[contracts.ReadinessMetadata]
    operations: MetadataRegistry[contracts.SummaryMetadata]
    workflows: MetadataRegistry[contracts.SummaryMetadata]
    runtime: MetadataRegistry[contracts.SummaryMetadata]
    resources: MetadataRegistry[contracts.SummaryMetadata]
    summaries: MetadataRegistry[contracts.SummaryMetadata]
    dependencies: MetadataRegistry[contracts.DependencyMetadata]
    capacity: MetadataRegistry[contracts.CapacityMetadata]
    recovery: MetadataRegistry[contracts.RecoveryMetadata]
    compatibility: MetadataRegistry[contracts.CompatibilityMetadata]
    health_records: MetadataRegistry[contracts.HealthMetadata]
    metric_records: MetadataRegistry[contracts.MetricMetadata]

    DEFINITIONS = (
        ("profiles", contracts.OperationProfile, "profile_id"),
        ("readiness", contracts.ReadinessMetadata, "readiness_id"),
        ("operations", contracts.SummaryMetadata, "summary_id"),
        ("workflows", contracts.SummaryMetadata, "summary_id"),
        ("runtime", contracts.SummaryMetadata, "summary_id"),
        ("resources", contracts.SummaryMetadata, "summary_id"),
        ("summaries", contracts.SummaryMetadata, "summary_id"),
        ("dependencies", contracts.DependencyMetadata, "dependency_id"),
        ("capacity", contracts.CapacityMetadata, "capacity_id"),
        ("recovery", contracts.RecoveryMetadata, "recovery_id"),
        ("compatibility", contracts.CompatibilityMetadata, "compatibility_id"),
        ("health_records", contracts.HealthMetadata, "health_id"),
        ("metric_records", contracts.MetricMetadata, "metric_id"),
    )

    def __init__(self) -> None:
        for name, _, identifier in self.DEFINITIONS:

            def identity(item: object, key: str = identifier) -> str:
                return str(getattr(item, key))

            setattr(self, name, MetadataRegistry(identity))


__all__ = ("MetadataRegistry", "OperationsRegistryCatalog")
