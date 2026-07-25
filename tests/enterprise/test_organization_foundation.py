"""Offline tests for Enterprise Organization Foundation contracts."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from enterprise.models import Department, Organization, Team, Workspace
from enterprise.organization import (
    Division,
    Membership,
    OrganizationContext,
    OrganizationDescriptor,
    OrganizationFactory,
    OrganizationGraph,
    OrganizationRegistry,
)
from enterprise.organization.errors import (
    OrganizationConflictError,
    OrganizationNotFoundError,
)


def _graph() -> OrganizationGraph:
    organization = Organization("org-1", "Example")
    division = Division("division-1", "org-1", "Engineering")
    department = Department("department-1", "org-1", "Platform")
    workspace = Workspace("workspace-1", "department-1", "Core")
    team = Team("team-1", "workspace-1", "Runtime")
    membership = Membership("member-1", "org-1", "user-1", "workspace-1", "team-1")
    return OrganizationGraph(
        {
            "org-1": organization,
            "division-1": division,
            "department-1": department,
            "workspace-1": workspace,
            "team-1": team,
        },
        {
            "org-1": ("division-1", "department-1"),
            "department-1": ("workspace-1",),
            "workspace-1": ("team-1",),
        },
        (membership,),
    )


def test_organization_graph_exposes_explicit_parent_child_and_membership() -> None:
    """Hierarchy and membership are read-only snapshots, not a repository."""
    graph = _graph()

    assert graph.children_of("org-1") == ("division-1", "department-1")
    assert graph.parent_of("team-1") == "workspace-1"
    assert graph.memberships_for("user-1")[0].team_id == "team-1"
    with pytest.raises(TypeError):
        graph.entities["other"] = graph.entities["org-1"]  # type: ignore[index]


def test_organization_graph_rejects_invalid_hierarchy_links() -> None:
    """Self-links and unknown graph references are rejected deterministically."""
    organization = Organization("org-1", "Example")

    with pytest.raises(ValueError, match="self-child"):
        OrganizationGraph({"org-1": organization}, {"org-1": ("org-1",)})
    with pytest.raises(ValueError, match="Unknown hierarchy child"):
        OrganizationGraph({"org-1": organization}, {"org-1": ("missing",)})


def test_context_descriptor_and_division_are_immutable_and_serializable() -> None:
    """Scope data is explicit and cannot leak mutable metadata state."""
    context = OrganizationContext("org-1", "workspace-1", metadata={"mode": "test"})
    descriptor = OrganizationDescriptor("org-1", "Example", {"hierarchy"})
    division = Division("division-1", "org-1", "Engineering")

    assert context.to_dict()["organization_id"] == "org-1"
    assert descriptor.capabilities == frozenset({"hierarchy"})
    with pytest.raises(FrozenInstanceError):
        division.name = "Changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        context.metadata["mode"] = "other"  # type: ignore[index]


def test_reference_organization_registry_requires_explicit_registration() -> None:
    """The registry has no default organization or hidden persistence behavior."""
    reference = OrganizationFactory.reference(
        OrganizationDescriptor("org-1", "Example"), _graph()
    )
    registry = OrganizationRegistry()

    registry.register(reference)

    assert registry.lookup("org-1").snapshot() == _graph()
    with pytest.raises(OrganizationConflictError):
        registry.register(reference)
    assert registry.unregister("org-1") is reference
    with pytest.raises(OrganizationNotFoundError):
        registry.lookup("org-1")


def test_organization_documentation_keeps_foundation_offline() -> None:
    """Documentation prevents callers from inferring repository functionality."""
    document = (
        __import__("pathlib").Path(__file__).parents[2] / "docs" / "Organization.md"
    ).read_text(encoding="utf-8")

    assert "No database" in document
    assert "No authentication" in document
    assert "ReferenceOrganization" in document
