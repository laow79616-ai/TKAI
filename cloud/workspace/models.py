"""Immutable Workspace Foundation descriptors with no invitation transport."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from ..models import CloudValue, snapshot


class WorkspaceRole(str, Enum):
    """Descriptive workspace roles; they do not enforce authorization."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class InvitationStatus(str, Enum):
    """Descriptive invitation lifecycle state with no delivery implementation."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class Membership:
    """Explicit principal-to-workspace membership descriptor."""

    workspace_id: str
    principal_id: str
    role: WorkspaceRole = WorkspaceRole.MEMBER
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workspace_id or not self.principal_id:
            raise ValueError(
                "Membership workspace and principal ids must not be empty."
            )
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class Invitation:
    """Invitation declaration that never sends mail, notifications, or network calls."""

    invitation_id: str
    workspace_id: str
    principal_id: str
    role: WorkspaceRole = WorkspaceRole.MEMBER
    status: InvitationStatus = InvitationStatus.PENDING
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.invitation_id or not self.workspace_id or not self.principal_id:
            raise ValueError(
                "Invitation, workspace, and principal ids must not be empty."
            )
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class WorkspaceDescriptor:
    """Capability declaration for a workspace without provisioning resources."""

    workspace_id: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, CloudValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.workspace_id:
            raise ValueError("Workspace descriptor requires a workspace id.")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "metadata", snapshot(self.metadata))
