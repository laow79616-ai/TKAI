"""Typed in-memory registries for immutable governance metadata."""

from __future__ import annotations

from collections.abc import Callable
from typing import Generic, TypeVar

from tkai.v8.hyper_governance.contracts import (
    ApprovalRecord,
    BoundaryRecord,
    CompatibilityRecord,
    ComplianceRecord,
    ConstraintRecord,
    GovernanceProfile,
    PolicyRecord,
    ReviewRecord,
)

T = TypeVar("T")


class MetadataRegistry(Generic[T]):
    """A deterministic registry that stores metadata records by identifier."""

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


class GovernanceRegistryCatalog:
    """All registries exposed by the governance fabric."""

    def __init__(self) -> None:
        self.profiles = MetadataRegistry[GovernanceProfile](
            lambda item: item.profile_id
        )
        self.policies = MetadataRegistry[PolicyRecord](lambda item: item.policy_id)
        self.constraints = MetadataRegistry[ConstraintRecord](
            lambda item: item.constraint_id
        )
        self.boundaries = MetadataRegistry[BoundaryRecord](
            lambda item: item.boundary_id
        )
        self.compliance = MetadataRegistry[ComplianceRecord](
            lambda item: item.compliance_id
        )
        self.reviews = MetadataRegistry[ReviewRecord](lambda item: item.review_id)
        self.approvals = MetadataRegistry[ApprovalRecord](lambda item: item.approval_id)
        self.compatibility = MetadataRegistry[CompatibilityRecord](
            lambda item: item.compatibility_id
        )


__all__ = ("GovernanceRegistryCatalog", "MetadataRegistry")
