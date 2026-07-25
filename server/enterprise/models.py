"""Immutable, JSON-safe Enterprise feature models with caller-supplied IDs/time."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType


def _metadata(values: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(sorted(values.items())))


@dataclass(frozen=True, slots=True)
class UserId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("User id is required.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class OrganizationId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Organization id is required.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class TeamId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Team id is required.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class RoleId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Role id is required.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class ApiKeyId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("API key id is required.")

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class AuditEventId:
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Audit event id is required.")

    def __str__(self) -> str:
        return self.value


class UserStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISABLED = "disabled"


class ApiKeyStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass(frozen=True, slots=True)
class UserRecord:
    user_id: UserId
    username: str
    status: UserStatus = UserStatus.ACTIVE
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.username:
            raise ValueError("Username is required.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "user_id": str(self.user_id),
            "username": self.username,
            "status": self.status.value,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class OrganizationRecord:
    organization_id: OrganizationId
    name: str
    active: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Organization name is required.")
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "organization_id": str(self.organization_id),
            "name": self.name,
            "active": self.active,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class TeamRecord:
    team_id: TeamId
    organization_id: OrganizationId
    name: str
    member_ids: tuple[UserId, ...] = ()
    active: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Team name is required.")
        object.__setattr__(
            self, "member_ids", tuple(sorted(set(self.member_ids), key=str))
        )
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "team_id": str(self.team_id),
            "organization_id": str(self.organization_id),
            "name": self.name,
            "members": [str(v) for v in self.member_ids],
            "active": self.active,
            "metadata": dict(self.metadata),
        }


Permission = str
ALL_PERMISSIONS = frozenset(
    {
        "registry.read",
        "registry.write",
        "publisher.read",
        "publisher.write",
        "package.read",
        "package.write",
        "version.read",
        "version.write",
        "search.read",
        "statistics.read",
        "health.read",
        "users.read",
        "users.write",
        "organizations.read",
        "organizations.write",
        "teams.read",
        "teams.write",
        "roles.read",
        "roles.write",
        "api_keys.read",
        "api_keys.write",
        "audit.read",
    }
)


@dataclass(frozen=True, slots=True)
class RoleRecord:
    role_id: RoleId
    name: str
    permissions: tuple[Permission, ...]
    organization_id: OrganizationId | None = None

    def __post_init__(self) -> None:
        if not self.name or not set(self.permissions).issubset(ALL_PERMISSIONS):
            raise ValueError("Role is invalid.")
        object.__setattr__(self, "permissions", tuple(sorted(set(self.permissions))))

    def to_dict(self) -> dict[str, object]:
        return {
            "role_id": str(self.role_id),
            "name": self.name,
            "permissions": list(self.permissions),
            "organization_id": (
                str(self.organization_id) if self.organization_id else None
            ),
        }


@dataclass(frozen=True, slots=True)
class RoleAssignment:
    user_id: UserId
    role_id: RoleId
    organization_id: OrganizationId | None = None


@dataclass(frozen=True, slots=True)
class ApiKeyRecord:
    api_key_id: ApiKeyId
    owner_id: UserId
    secret_digest: str = field(repr=False)
    scopes: tuple[Permission, ...] = ()
    organization_id: OrganizationId | None = None
    expires_at: str | None = None
    status: ApiKeyStatus = ApiKeyStatus.ACTIVE

    def __post_init__(self) -> None:
        if not self.secret_digest or not set(self.scopes).issubset(ALL_PERMISSIONS):
            raise ValueError("API key is invalid.")
        object.__setattr__(self, "scopes", tuple(sorted(set(self.scopes))))

    def to_dict(self) -> dict[str, object]:
        return {
            "api_key_id": str(self.api_key_id),
            "owner_id": str(self.owner_id),
            "scopes": list(self.scopes),
            "organization_id": (
                str(self.organization_id) if self.organization_id else None
            ),
            "expires_at": self.expires_at,
            "status": self.status.value,
        }


class AuditAction(str, Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_SUSPENDED = "user_suspended"
    ORGANIZATION_CREATED = "organization_created"
    ORGANIZATION_UPDATED = "organization_updated"
    TEAM_CREATED = "team_created"
    TEAM_MEMBERSHIP_CHANGED = "team_membership_changed"
    ROLE_ASSIGNED = "role_assigned"
    ROLE_REMOVED = "role_removed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    PERMISSION_DENIED = "permission_denied"


@dataclass(frozen=True, slots=True)
class AuditTarget:
    kind: str
    identifier: str


@dataclass(frozen=True, slots=True)
class AuditEvent:
    event_id: AuditEventId
    action: AuditAction
    actor_id: UserId | None
    target: AuditTarget
    timestamp: str
    outcome: str
    sequence: int
    organization_id: OrganizationId | None = None
    request_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _metadata(self.metadata))

    def to_dict(self) -> dict[str, object]:
        return {
            "event_id": str(self.event_id),
            "action": self.action.value,
            "actor_id": str(self.actor_id) if self.actor_id else None,
            "target": {"kind": self.target.kind, "identifier": self.target.identifier},
            "timestamp": self.timestamp,
            "outcome": self.outcome,
            "sequence": self.sequence,
            "organization_id": (
                str(self.organization_id) if self.organization_id else None
            ),
            "request_id": self.request_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class EnterpriseStatistics:
    users: int = 0
    organizations: int = 0
    teams: int = 0
    roles: int = 0
    api_keys: int = 0
    audit_events: int = 0


@dataclass(frozen=True, slots=True)
class EnterpriseSnapshot:
    users: tuple[UserRecord, ...] = ()
    organizations: tuple[OrganizationRecord, ...] = ()
    teams: tuple[TeamRecord, ...] = ()
    roles: tuple[RoleRecord, ...] = ()
    api_keys: tuple[ApiKeyRecord, ...] = ()
    audit_events: tuple[AuditEvent, ...] = ()
    statistics: EnterpriseStatistics = EnterpriseStatistics()
    closed: bool = False
