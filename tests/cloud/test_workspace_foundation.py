"""Offline tests for the Cloud Workspace Foundation reference layer."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError

import pytest

from cloud.workspace import (
    Invitation,
    Membership,
    ReferenceWorkspaceService,
    WorkspaceDescriptor,
    WorkspaceGraph,
    WorkspaceRegistry,
    WorkspaceRole,
)
from cloud.workspace.errors import WorkspaceConflictError, WorkspaceNotFoundError


def test_reference_workspace_service_creates_and_filters_workspaces() -> None:
    """Reference workspaces have explicit account ownership and stable ordering."""
    service = ReferenceWorkspaceService()
    service.create("workspace-b", "account-1", "B")
    service.create("workspace-a", "account-1", "A")
    service.create("workspace-c", "account-2", "C")

    assert [item.workspace_id for item in service.workspaces("account-1")] == [
        "workspace-a",
        "workspace-b",
    ]
    assert service.workspace("workspace-c").account_id == "account-2"


def test_membership_and_invitation_are_local_immutable_declarations() -> None:
    """Memberships and invitations do not resolve identities or send messages."""
    service = ReferenceWorkspaceService()
    service.create("workspace-1", "account-1", "Workspace")
    membership = Membership("workspace-1", "principal-1", WorkspaceRole.OWNER)
    invitation = Invitation("invite-1", "workspace-1", "principal-2")

    assert service.add_membership(membership) is membership
    assert service.add_invitation(invitation) is invitation
    assert service.memberships("workspace-1") == (membership,)
    with pytest.raises(FrozenInstanceError):
        membership.principal_id = "other"  # type: ignore[misc]


def test_workspace_registry_rejects_unknown_and_duplicate_resources() -> None:
    """Registry behavior remains explicit and does not infer missing workspace scope."""
    service = ReferenceWorkspaceService()
    service.create("workspace-1", "account-1", "Workspace")

    with pytest.raises(WorkspaceConflictError):
        service.create("workspace-1", "account-1", "Duplicate")
    with pytest.raises(WorkspaceNotFoundError):
        service.memberships("missing")
    with pytest.raises(WorkspaceNotFoundError):
        service.add_membership(Membership("missing", "principal"))


def test_workspace_graph_projects_account_workspace_and_memberships() -> None:
    """Graph output is stable, serializable, and contains no global state."""
    service = ReferenceWorkspaceService()
    workspace = service.create("workspace-1", "account-1", "Workspace")
    service.add_membership(Membership("workspace-1", "principal-b"))
    service.add_membership(Membership("workspace-1", "principal-a"))

    graph = WorkspaceGraph.snapshot(workspace, service.memberships("workspace-1"))

    assert graph.nodes == ("account-1", "workspace-1", "principal-a", "principal-b")
    assert graph.to_dict()["edges"] == [
        ["account-1", "workspace-1"],
        ["workspace-1", "principal-a"],
        ["workspace-1", "principal-b"],
    ]


def test_workspace_descriptor_and_service_cleanup_are_defensive() -> None:
    """Descriptors snapshot inputs and close clears local state idempotently."""
    source = {"scope": "reference"}
    descriptor = WorkspaceDescriptor(
        "workspace-1", capabilities={"memberships"}, metadata=source
    )
    source["scope"] = "changed"
    service = ReferenceWorkspaceService()
    service.create("workspace-1", "account-1", "Workspace")
    service.close()
    service.close()

    assert dict(descriptor.metadata) == {"scope": "reference"}
    assert service.workspaces() == ()


def test_workspace_registry_is_safe_for_bounded_concurrent_reference_writes() -> None:
    """Registry locking preserves each independently registered workspace."""
    registry = WorkspaceRegistry()
    service = ReferenceWorkspaceService(registry=registry)

    with ThreadPoolExecutor(max_workers=4) as executor:
        list(
            executor.map(
                lambda index: service.create(
                    f"workspace-{index}", "account-1", f"Workspace {index}"
                ),
                range(8),
            )
        )

    assert len(service.workspaces("account-1")) == 8
