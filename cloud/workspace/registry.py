"""Thread-safe in-memory workspace registry for offline reference use only."""

from __future__ import annotations

from threading import RLock

from ..models import Workspace
from .errors import WorkspaceConflictError, WorkspaceNotFoundError
from .models import Invitation, Membership


class WorkspaceRegistry:
    """Maintain local workspace, membership, and invitation snapshots."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._workspaces: dict[str, Workspace] = {}
        self._memberships: dict[tuple[str, str], Membership] = {}
        self._invitations: dict[str, Invitation] = {}

    def register(self, workspace: Workspace) -> Workspace:
        """Register an immutable workspace or raise on a duplicate identifier."""
        with self._lock:
            if workspace.workspace_id in self._workspaces:
                raise WorkspaceConflictError(workspace.workspace_id)
            self._workspaces[workspace.workspace_id] = workspace
            return workspace

    def unregister(self, workspace_id: str) -> Workspace:
        """Remove a workspace and its associated reference-only relationships."""
        with self._lock:
            try:
                workspace = self._workspaces.pop(workspace_id)
            except KeyError as exc:
                raise WorkspaceNotFoundError(workspace_id) from exc
            self._memberships = {
                key: value
                for key, value in self._memberships.items()
                if value.workspace_id != workspace_id
            }
            self._invitations = {
                key: value
                for key, value in self._invitations.items()
                if value.workspace_id != workspace_id
            }
            return workspace

    def get(self, workspace_id: str) -> Workspace:
        """Return a registered immutable workspace."""
        with self._lock:
            try:
                return self._workspaces[workspace_id]
            except KeyError as exc:
                raise WorkspaceNotFoundError(workspace_id) from exc

    def list(self, account_id: str | None = None) -> tuple[Workspace, ...]:
        """Return stable workspace snapshots, optionally filtered by account."""
        with self._lock:
            return tuple(
                workspace
                for _, workspace in sorted(self._workspaces.items())
                if account_id is None or workspace.account_id == account_id
            )

    def add_membership(self, membership: Membership) -> Membership:
        """Store an explicit membership after verifying its workspace exists."""
        with self._lock:
            if membership.workspace_id not in self._workspaces:
                raise WorkspaceNotFoundError(membership.workspace_id)
            self._memberships[(membership.workspace_id, membership.principal_id)] = (
                membership
            )
            return membership

    def memberships(self, workspace_id: str) -> tuple[Membership, ...]:
        """Return memberships in stable principal order."""
        with self._lock:
            if workspace_id not in self._workspaces:
                raise WorkspaceNotFoundError(workspace_id)
            return tuple(
                membership
                for _, membership in sorted(self._memberships.items())
                if membership.workspace_id == workspace_id
            )

    def add_invitation(self, invitation: Invitation) -> Invitation:
        """Store an invitation declaration without delivering it."""
        with self._lock:
            if invitation.workspace_id not in self._workspaces:
                raise WorkspaceNotFoundError(invitation.workspace_id)
            if invitation.invitation_id in self._invitations:
                raise WorkspaceConflictError(invitation.invitation_id)
            self._invitations[invitation.invitation_id] = invitation
            return invitation

    def invitations(self, workspace_id: str) -> tuple[Invitation, ...]:
        """Return invitations in stable identifier order."""
        with self._lock:
            if workspace_id not in self._workspaces:
                raise WorkspaceNotFoundError(workspace_id)
            return tuple(
                invitation
                for _, invitation in sorted(self._invitations.items())
                if invitation.workspace_id == workspace_id
            )

    def clear(self) -> None:
        """Idempotently clear all local reference state."""
        with self._lock:
            self._workspaces.clear()
            self._memberships.clear()
            self._invitations.clear()
