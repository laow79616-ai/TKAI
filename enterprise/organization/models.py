"""Immutable Organization Foundation models built on existing Enterprise entities."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ..models import Department, Organization, Team, Workspace

OrganizationValue = str | int | float | bool | None


def _snapshot(
    value: Mapping[str, OrganizationValue],
) -> Mapping[str, OrganizationValue]:
    """Return a defensive, read-only mapping snapshot."""
    return MappingProxyType(dict(value))


@dataclass(frozen=True, slots=True)
class Division:
    """A named organization child used to describe business hierarchy only."""

    division_id: str
    organization_id: str
    name: str
    parent_id: str | None = None
    metadata: Mapping[str, OrganizationValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.division_id or not self.organization_id or not self.name:
            raise ValueError(
                "Division id, organization id, and name must not be empty."
            )
        if self.parent_id == self.division_id:
            raise ValueError("Division cannot be its own parent.")
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


OrganizationEntity = Organization | Division | Department | Workspace | Team


@dataclass(frozen=True, slots=True)
class Membership:
    """A non-authenticating principal membership in an organization boundary."""

    membership_id: str
    organization_id: str
    principal_id: str
    workspace_id: str | None = None
    team_id: str | None = None
    role_ids: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, OrganizationValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.membership_id or not self.organization_id or not self.principal_id:
            raise ValueError(
                "Membership id, organization id, and principal id are required."
            )
        object.__setattr__(self, "role_ids", frozenset(self.role_ids))
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class OrganizationContext:
    """Explicit organization scope with no ambient request, tenant, or identity lookup.

    The context carries only caller-provided identifiers and safe metadata.
    """

    organization_id: str
    workspace_id: str | None = None
    team_id: str | None = None
    membership_id: str | None = None
    metadata: Mapping[str, OrganizationValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.organization_id:
            raise ValueError("Organization context requires an organization id.")
        object.__setattr__(self, "metadata", _snapshot(self.metadata))

    def to_dict(self) -> dict[str, object]:
        """Return a stable JSON-safe scope snapshot."""
        return {
            "organization_id": self.organization_id,
            "workspace_id": self.workspace_id,
            "team_id": self.team_id,
            "membership_id": self.membership_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class OrganizationDescriptor:
    """Describes an organization component without storage configuration or secrets."""

    organization_id: str
    name: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, OrganizationValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.organization_id or not self.name:
            raise ValueError("Organization descriptor id and name must not be empty.")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "metadata", _snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class OrganizationGraph:
    """A read-only parent/child hierarchy and membership snapshot."""

    entities: Mapping[str, OrganizationEntity] = field(default_factory=dict)
    children: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    memberships: tuple[Membership, ...] = ()

    def __post_init__(self) -> None:
        entities = dict(self.entities)
        children = {
            parent_id: tuple(child_ids)
            for parent_id, child_ids in self.children.items()
        }
        parents: dict[str, str] = {}
        for parent_id, child_ids in children.items():
            if parent_id not in entities:
                raise ValueError(f"Unknown hierarchy parent {parent_id!r}.")
            for child_id in child_ids:
                if parent_id == child_id:
                    raise ValueError(
                        "Organization graph cannot contain self-child links."
                    )
                if child_id not in entities:
                    raise ValueError(f"Unknown hierarchy child {child_id!r}.")
                if child_id in parents:
                    raise ValueError(
                        f"Hierarchy child {child_id!r} has multiple parents."
                    )
                parents[child_id] = parent_id
        object.__setattr__(self, "entities", MappingProxyType(entities))
        object.__setattr__(self, "children", MappingProxyType(children))
        object.__setattr__(self, "memberships", tuple(self.memberships))

    def children_of(self, entity_id: str) -> tuple[str, ...]:
        """Return immutable, deterministic children for an entity."""
        return self.children.get(entity_id, ())

    def parent_of(self, entity_id: str) -> str | None:
        """Return a hierarchy parent without exposing internal mutable state."""
        for parent_id, child_ids in self.children.items():
            if entity_id in child_ids:
                return parent_id
        return None

    def memberships_for(self, principal_id: str) -> tuple[Membership, ...]:
        """Return memberships for an explicitly supplied principal id."""
        return tuple(
            membership
            for membership in self.memberships
            if membership.principal_id == principal_id
        )
