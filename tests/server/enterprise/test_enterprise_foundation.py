"""Offline Enterprise foundation coverage."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from server.enterprise import (
    ReferenceEnterpriseService,
)
from server.enterprise.errors import (
    EnterpriseAuthenticationError,
    EnterpriseClosedError,
    EnterpriseConflictError,
)
from server.enterprise.models import (
    ApiKeyId,
    OrganizationId,
    OrganizationRecord,
    RoleAssignment,
    TeamId,
    TeamRecord,
    UserId,
    UserRecord,
)

TIME = "2026-07-25T00:00:00Z"


def service() -> ReferenceEnterpriseService:
    return ReferenceEnterpriseService(secret_factory=lambda: "once-only-secret")


def test_user_organization_team_rbac_audit_and_snapshot() -> None:
    value = service()
    user = value.create_user(UserRecord(UserId("u1"), "alice"), "password", TIME)
    assert value.verify_credentials("alice", "password") == user
    organization = value.create_organization(
        OrganizationRecord(OrganizationId("o1"), "One"), TIME
    )
    team = value.create_team(
        TeamRecord(TeamId("t1"), organization.organization_id, "Team"), TIME
    )
    assert value.add_team_member(
        str(team.team_id), str(user.user_id), TIME
    ).member_ids == (user.user_id,)
    roles = value.initialize_builtin_roles()
    value.assign_role(RoleAssignment(user.user_id, roles[0].role_id), TIME)
    assert value.authorization.allowed(
        user.user_id, "users.write", value.roles(), value.storage.assignments()
    )
    snapshot = value.snapshot()
    assert (
        snapshot.users[0].username == "alice" and snapshot.audit_events[0].sequence == 1
    )


def test_duplicates_passwords_keys_and_close_are_safe() -> None:
    value = service()
    user = UserRecord(UserId("u1"), "alice")
    value.create_user(user, "password", TIME)
    with pytest.raises(EnterpriseConflictError):
        value.create_user(user, "password", TIME)
    with pytest.raises(EnterpriseAuthenticationError):
        value.verify_credentials("alice", "wrong")
    record, secret = value.create_api_key(
        ApiKeyId("k1"), user.user_id, ("users.read",), TIME
    )
    assert secret == "once-only-secret" and "secret_digest" not in record.to_dict()
    assert value.verify_api_key("k1", secret) == record
    assert value.revoke_api_key("k1", TIME).status.value == "revoked"
    with pytest.raises(EnterpriseAuthenticationError):
        value.verify_api_key("k1", secret)
    value.close()
    value.close()
    with pytest.raises(EnterpriseClosedError):
        value.list_users()


def test_reference_storage_is_instance_isolated_and_concurrent() -> None:
    first = service()
    second = service()

    def create(index: int) -> None:
        first.create_user(
            UserRecord(UserId(f"u{index}"), f"user{index}"), "password", TIME
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(create, range(32)))
    assert len(first.list_users()) == 32 and second.list_users() == ()
