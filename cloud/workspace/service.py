"""Explicit Workspace service contracts and local reference implementation."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from ..models import CloudValue, Workspace
from .factory import WorkspaceFactory
from .models import Invitation, Membership
from .registry import WorkspaceRegistry


class WorkspaceService(Protocol):
    """Future workspace service boundary with no API server or persistence."""

    def workspace(self, workspace_id: str) -> Workspace: ...
    def workspaces(self, account_id: str | None = None) -> tuple[Workspace, ...]: ...
    def memberships(self, workspace_id: str) -> tuple[Membership, ...]: ...


class ReferenceWorkspaceService:
    """Offline in-memory Workspace service requiring explicit collaborators."""

    def __init__(
        self,
        registry: WorkspaceRegistry | None = None,
        factory: WorkspaceFactory | None = None,
    ) -> None:
        self._registry = registry if registry is not None else WorkspaceRegistry()
        self._factory = factory if factory is not None else WorkspaceFactory()

    @property
    def registry(self) -> WorkspaceRegistry:
        """Expose the explicit local registry for lifecycle management."""
        return self._registry

    def create(
        self,
        workspace_id: str,
        account_id: str,
        name: str,
        *,
        region: str | None = None,
        metadata: Mapping[str, CloudValue] | None = None,
    ) -> Workspace:
        """Construct and register a local reference workspace."""
        workspace = self._factory.create(
            workspace_id, account_id, name, region=region, metadata=metadata
        )
        return self._registry.register(workspace)

    def workspace(self, workspace_id: str) -> Workspace:
        """Return a local workspace snapshot."""
        return self._registry.get(workspace_id)

    def workspaces(self, account_id: str | None = None) -> tuple[Workspace, ...]:
        """Return local workspace snapshots in stable order."""
        return self._registry.list(account_id)

    def add_membership(self, membership: Membership) -> Membership:
        """Add a local membership without any external identity resolution."""
        return self._registry.add_membership(membership)

    def memberships(self, workspace_id: str) -> tuple[Membership, ...]:
        """Return local membership snapshots."""
        return self._registry.memberships(workspace_id)

    def add_invitation(self, invitation: Invitation) -> Invitation:
        """Record a local invitation declaration without sending it."""
        return self._registry.add_invitation(invitation)

    def close(self) -> None:
        """Idempotently release all in-memory reference state."""
        self._registry.clear()
