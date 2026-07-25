"""Explicit Enterprise services over the reference storage boundary."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from hashlib import pbkdf2_hmac
from hmac import compare_digest
from secrets import token_bytes, token_urlsafe
from typing import cast

from .errors import EnterpriseAuthenticationError
from .models import (
    ApiKeyId,
    ApiKeyRecord,
    ApiKeyStatus,
    AuditAction,
    AuditEvent,
    AuditEventId,
    AuditTarget,
    OrganizationRecord,
    RoleAssignment,
    RoleRecord,
    TeamRecord,
    UserId,
    UserRecord,
    UserStatus,
)
from .permissions import AuthorizationService, builtin_roles
from .protocols import PasswordHasher, UserDirectory
from .storage import ReferenceEnterpriseStorage


class PBKDF2PasswordHasher:
    """Standard-library PBKDF2 password hashing; plaintext is never retained."""

    def __init__(self, salt_factory: Callable[[int], bytes] = token_bytes) -> None:
        self._salt_factory = salt_factory

    def hash(self, password: str) -> str:
        if not password:
            raise EnterpriseAuthenticationError("Invalid credentials.")
        salt = self._salt_factory(16)
        digest = pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
        return f"pbkdf2_sha256$200000${salt.hex()}${digest.hex()}"

    def verify(self, password: str, digest: str) -> bool:
        try:
            algorithm, rounds, salt, expected = digest.split("$")
            calculated = pbkdf2_hmac(
                "sha256", password.encode(), bytes.fromhex(salt), int(rounds)
            ).hex()
            return algorithm == "pbkdf2_sha256" and compare_digest(calculated, expected)
        except (ValueError, TypeError):
            return False


class ReferenceEnterpriseService(UserDirectory):
    """Coordinate enterprise writes with deterministic audit records and no sessions."""

    def __init__(
        self,
        storage: ReferenceEnterpriseStorage | None = None,
        hasher: PasswordHasher | None = None,
        secret_factory: Callable[[], str] = token_urlsafe,
    ) -> None:
        self.storage = storage or ReferenceEnterpriseStorage()
        self._hasher = hasher or PBKDF2PasswordHasher()
        self._secret_factory = secret_factory
        self.authorization = AuthorizationService()

    def create_user(
        self, user: UserRecord, password: str, timestamp: str
    ) -> UserRecord:
        result = self.storage.create("users", user, str(user.user_id))
        self._credentials()[str(user.user_id)] = self._hasher.hash(password)
        self._audit(
            AuditAction.USER_CREATED, None, "user", str(user.user_id), timestamp
        )
        return cast(UserRecord, result)

    def update_user(self, user: UserRecord, timestamp: str) -> UserRecord:
        result = self.storage.update("users", user, str(user.user_id))
        self._audit(
            AuditAction.USER_UPDATED, user.user_id, "user", str(user.user_id), timestamp
        )
        return cast(UserRecord, result)

    def suspend_user(self, user_id: str, timestamp: str) -> UserRecord:
        return self._state(user_id, UserStatus.SUSPENDED, timestamp)

    def restore_user(self, user_id: str, timestamp: str) -> UserRecord:
        return self._state(user_id, UserStatus.ACTIVE, timestamp)

    def disable_user(self, user_id: str, timestamp: str) -> UserRecord:
        return self._state(user_id, UserStatus.DISABLED, timestamp)

    def get_user(self, user_id: str) -> UserRecord:
        return cast(UserRecord, self.storage.get("users", user_id))

    def list_users(self) -> tuple[UserRecord, ...]:
        return cast(tuple[UserRecord, ...], self.storage.list("users"))

    def verify_credentials(self, username: str, password: str) -> UserRecord:
        for user in self.list_users():
            if (
                user.username == username
                and user.status is UserStatus.ACTIVE
                and self._hasher.verify(
                    password, self._credentials().get(str(user.user_id), "")
                )
            ):
                return user
        raise EnterpriseAuthenticationError("Invalid credentials.")

    def create_organization(
        self, value: OrganizationRecord, timestamp: str
    ) -> OrganizationRecord:
        result = self.storage.create("organizations", value, str(value.organization_id))
        self._audit(
            AuditAction.ORGANIZATION_CREATED,
            None,
            "organization",
            str(value.organization_id),
            timestamp,
        )
        return cast(OrganizationRecord, result)

    def update_organization(
        self, value: OrganizationRecord, timestamp: str
    ) -> OrganizationRecord:
        result = self.storage.update("organizations", value, str(value.organization_id))
        self._audit(
            AuditAction.ORGANIZATION_UPDATED,
            None,
            "organization",
            str(value.organization_id),
            timestamp,
        )
        return cast(OrganizationRecord, result)

    def organizations(self) -> tuple[OrganizationRecord, ...]:
        return cast(tuple[OrganizationRecord, ...], self.storage.list("organizations"))

    def get_organization(self, organization_id: str) -> OrganizationRecord:
        return cast(
            OrganizationRecord, self.storage.get("organizations", organization_id)
        )

    def create_team(self, value: TeamRecord, timestamp: str) -> TeamRecord:
        self.storage.get("organizations", str(value.organization_id))
        result = self.storage.create("teams", value, str(value.team_id))
        self._audit(
            AuditAction.TEAM_CREATED, None, "team", str(value.team_id), timestamp
        )
        return cast(TeamRecord, result)

    def update_team(self, value: TeamRecord, timestamp: str) -> TeamRecord:
        result = self.storage.update("teams", value, str(value.team_id))
        self._audit(
            AuditAction.TEAM_MEMBERSHIP_CHANGED,
            None,
            "team",
            str(value.team_id),
            timestamp,
        )
        return cast(TeamRecord, result)

    def add_team_member(self, team_id: str, user_id: str, timestamp: str) -> TeamRecord:
        team = cast(TeamRecord, self.storage.get("teams", team_id))
        user = self.get_user(user_id)
        result = replace(team, member_ids=team.member_ids + (user.user_id,))
        return self.update_team(result, timestamp)

    def remove_team_member(
        self, team_id: str, user_id: str, timestamp: str
    ) -> TeamRecord:
        team = cast(TeamRecord, self.storage.get("teams", team_id))
        result = replace(
            team,
            member_ids=tuple(item for item in team.member_ids if str(item) != user_id),
        )
        return self.update_team(result, timestamp)

    def teams(self) -> tuple[TeamRecord, ...]:
        return cast(tuple[TeamRecord, ...], self.storage.list("teams"))

    def get_team(self, team_id: str) -> TeamRecord:
        return cast(TeamRecord, self.storage.get("teams", team_id))

    def create_role(self, value: RoleRecord) -> RoleRecord:
        return cast(RoleRecord, self.storage.create("roles", value, str(value.role_id)))

    def roles(self) -> tuple[RoleRecord, ...]:
        return cast(tuple[RoleRecord, ...], self.storage.list("roles"))

    def get_role(self, role_id: str) -> RoleRecord:
        return cast(RoleRecord, self.storage.get("roles", role_id))

    def assign_role(self, assignment: RoleAssignment, timestamp: str) -> None:
        self.get_user(str(assignment.user_id))
        self.storage.get("roles", str(assignment.role_id))
        self.storage.add_assignment(assignment)
        self._audit(
            AuditAction.ROLE_ASSIGNED,
            assignment.user_id,
            "role",
            str(assignment.role_id),
            timestamp,
        )

    def remove_role(self, assignment: RoleAssignment, timestamp: str) -> None:
        self.storage.remove_assignment(assignment)
        self._audit(
            AuditAction.ROLE_REMOVED,
            assignment.user_id,
            "role",
            str(assignment.role_id),
            timestamp,
        )

    def initialize_builtin_roles(self) -> tuple[RoleRecord, ...]:
        created = []
        for role in builtin_roles():
            try:
                created.append(self.create_role(role))
            except Exception:
                created.append(
                    cast(RoleRecord, self.storage.get("roles", str(role.role_id)))
                )
        return tuple(created)

    def create_api_key(
        self,
        key_id: ApiKeyId,
        owner_id: UserId,
        scopes: tuple[str, ...],
        timestamp: str,
        expires_at: str | None = None,
    ) -> tuple[ApiKeyRecord, str]:
        self.get_user(str(owner_id))
        secret = self._secret_factory()
        record = ApiKeyRecord(
            key_id, owner_id, self._hasher.hash(secret), scopes, expires_at=expires_at
        )
        self.storage.create("api_keys", record, str(key_id))
        self._audit(
            AuditAction.API_KEY_CREATED, owner_id, "api_key", str(key_id), timestamp
        )
        return record, secret

    def list_api_keys(self) -> tuple[ApiKeyRecord, ...]:
        return cast(tuple[ApiKeyRecord, ...], self.storage.list("api_keys"))

    def verify_api_key(
        self, key_id: str, secret: str, now: str | None = None
    ) -> ApiKeyRecord:
        record = cast(ApiKeyRecord, self.storage.get("api_keys", key_id))
        if (
            record.status is not ApiKeyStatus.ACTIVE
            or (record.expires_at and now is not None and now >= record.expires_at)
            or not self._hasher.verify(secret, record.secret_digest)
        ):
            raise EnterpriseAuthenticationError("API key is invalid.")
        return record

    def revoke_api_key(self, key_id: str, timestamp: str) -> ApiKeyRecord:
        record = cast(ApiKeyRecord, self.storage.get("api_keys", key_id))
        if record.status is ApiKeyStatus.REVOKED:
            return record
        revoked = replace(record, status=ApiKeyStatus.REVOKED)
        self.storage.update("api_keys", revoked, key_id)
        self._audit(
            AuditAction.API_KEY_REVOKED, record.owner_id, "api_key", key_id, timestamp
        )
        return revoked

    def snapshot(self) -> object:
        return self.storage.snapshot()

    def close(self) -> None:
        self.storage.close()

    def _state(self, user_id: str, status: UserStatus, timestamp: str) -> UserRecord:
        current = self.get_user(user_id)
        result = self.storage.update("users", replace(current, status=status), user_id)
        self._audit(
            AuditAction.USER_SUSPENDED, current.user_id, "user", user_id, timestamp
        )
        return cast(UserRecord, result)

    def _audit(
        self,
        action: AuditAction,
        actor: UserId | None,
        kind: str,
        identifier: str,
        timestamp: str,
    ) -> None:
        sequence = len(self.storage.audit()) + 1
        event = AuditEvent(
            AuditEventId(f"audit-{sequence}"),
            action,
            actor,
            AuditTarget(kind, identifier),
            timestamp,
            "success",
            sequence,
        )
        self.storage.append_audit(event)

    def _credentials(self) -> dict[str, str]:
        return self.storage._credentials
