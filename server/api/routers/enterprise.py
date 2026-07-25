"""Enterprise HTTP contracts delegated to one authenticated RBAC bridge."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from server.enterprise import (
    ApiKeyId,
    OrganizationId,
    OrganizationRecord,
    RoleAssignment,
    RoleId,
    RoleRecord,
    TeamId,
    TeamRecord,
    UserId,
    UserRecord,
)
from server.enterprise.permissions import PermissionEvaluator


class UserRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    user_id: str = Field(min_length=1)
    username: str = Field(min_length=1)
    password: str = Field(min_length=1, repr=False)
    timestamp: str = Field(min_length=1)


class OrganizationRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    organization_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)


class TeamRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    team_id: str = Field(min_length=1)
    organization_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)


class AssignmentRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    user_id: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)


class ApiKeyRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    api_key_id: str = Field(min_length=1)
    owner_id: str = Field(min_length=1)
    scopes: tuple[str, ...] = ()
    timestamp: str = Field(min_length=1)
    expires_at: str | None = None


class EnterpriseApiBridge:
    """Bridge authentication, PermissionEvaluator, and Enterprise Service."""

    def __init__(self, service: Any, authentication: Any) -> None:
        self._service = service
        self._authentication = authentication
        self._evaluator = PermissionEvaluator(service.authorization)

    def _require(self, authorization: str | None, permission: str) -> None:
        token = authorization.removeprefix("Bearer ") if authorization else ""
        authenticated = self._authentication.verify_token(token).user
        self._evaluator.require(
            UserId(authenticated.username),
            permission,
            self._service.roles(),
            self._service.storage.assignments(),
            legacy_administrator=authenticated.administrator,
        )

    def list_users(self, authorization: str | None = None) -> dict[str, object]:
        self._require(authorization, "users.read")
        return _list(self._service.list_users())

    def get_user(
        self, user_id: str, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "users.read")
        return {"data": self._service.get_user(user_id).to_dict(), "error": None}

    def create_user(
        self, request: UserRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "users.write")
        return {
            "data": self._service.create_user(
                UserRecord(UserId(request.user_id), request.username),
                request.password,
                request.timestamp,
            ).to_dict(),
            "error": None,
        }

    def update_user(
        self, user_id: str, request: UserRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "users.write")
        return {
            "data": self._service.update_user(
                UserRecord(UserId(user_id), request.username), request.timestamp
            ).to_dict(),
            "error": None,
        }

    def suspend(
        self, user_id: str, request: AssignmentRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "users.write")
        return {
            "data": self._service.suspend_user(user_id, request.timestamp).to_dict(),
            "error": None,
        }

    def restore(
        self, user_id: str, request: AssignmentRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "users.write")
        return {
            "data": self._service.restore_user(user_id, request.timestamp).to_dict(),
            "error": None,
        }

    def list_organizations(self, authorization: str | None = None) -> dict[str, object]:
        self._require(authorization, "organizations.read")
        return _list(self._service.organizations())

    def get_organization(
        self, organization_id: str, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "organizations.read")
        return {
            "data": self._service.get_organization(organization_id).to_dict(),
            "error": None,
        }

    def create_organization(
        self, request: OrganizationRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "organizations.write")
        return {
            "data": self._service.create_organization(
                OrganizationRecord(
                    OrganizationId(request.organization_id), request.name
                ),
                request.timestamp,
            ).to_dict(),
            "error": None,
        }

    def update_organization(
        self,
        organization_id: str,
        request: OrganizationRequest,
        authorization: str | None = None,
    ) -> dict[str, object]:
        self._require(authorization, "organizations.write")
        return {
            "data": self._service.update_organization(
                OrganizationRecord(OrganizationId(organization_id), request.name),
                request.timestamp,
            ).to_dict(),
            "error": None,
        }

    def list_teams(self, authorization: str | None = None) -> dict[str, object]:
        self._require(authorization, "teams.read")
        return _list(self._service.teams())

    def get_team(
        self, team_id: str, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "teams.read")
        return {"data": self._service.get_team(team_id).to_dict(), "error": None}

    def create_team(
        self, request: TeamRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "teams.write")
        return {
            "data": self._service.create_team(
                TeamRecord(
                    TeamId(request.team_id),
                    OrganizationId(request.organization_id),
                    request.name,
                ),
                request.timestamp,
            ).to_dict(),
            "error": None,
        }

    def update_team(
        self, team_id: str, request: TeamRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "teams.write")
        return {
            "data": self._service.update_team(
                TeamRecord(
                    TeamId(team_id),
                    OrganizationId(request.organization_id),
                    request.name,
                ),
                request.timestamp,
            ).to_dict(),
            "error": None,
        }

    def add_member(
        self, team_id: str, request: AssignmentRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "teams.write")
        return {
            "data": self._service.add_team_member(
                team_id, request.user_id, request.timestamp
            ).to_dict(),
            "error": None,
        }

    def remove_member(
        self,
        team_id: str,
        user_id: str,
        request: AssignmentRequest,
        authorization: str | None = None,
    ) -> dict[str, object]:
        self._require(authorization, "teams.write")
        return {
            "data": self._service.remove_team_member(
                team_id, user_id, request.timestamp
            ).to_dict(),
            "error": None,
        }

    def list_roles(self, authorization: str | None = None) -> dict[str, object]:
        self._require(authorization, "roles.read")
        return _list(self._service.roles())

    def create_role(
        self, request: Any, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "roles.write")
        return {
            "data": self._service.create_role(
                RoleRecord(
                    RoleId(request.role_id), request.name, tuple(request.permissions)
                )
            ).to_dict(),
            "error": None,
        }

    def assign_role(
        self, role_id: str, request: AssignmentRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "roles.write")
        self._service.assign_role(
            RoleAssignment(UserId(request.user_id), RoleId(role_id)), request.timestamp
        )
        return {"data": {"assigned": True}, "error": None}

    def remove_role(
        self,
        role_id: str,
        user_id: str,
        request: AssignmentRequest,
        authorization: str | None = None,
    ) -> dict[str, object]:
        self._require(authorization, "roles.write")
        self._service.remove_role(
            RoleAssignment(UserId(user_id), RoleId(role_id)), request.timestamp
        )
        return {"data": {"removed": True}, "error": None}

    def list_keys(self, authorization: str | None = None) -> dict[str, object]:
        self._require(authorization, "api_keys.read")
        return _list(self._service.list_api_keys())

    def create_key(
        self, request: ApiKeyRequest, authorization: str | None = None
    ) -> dict[str, object]:
        self._require(authorization, "api_keys.write")
        record, secret = self._service.create_api_key(
            ApiKeyId(request.api_key_id),
            UserId(request.owner_id),
            request.scopes,
            request.timestamp,
            request.expires_at,
        )
        return {"data": {**record.to_dict(), "secret": secret}, "error": None}

    def revoke_key(
        self,
        api_key_id: str,
        request: AssignmentRequest,
        authorization: str | None = None,
    ) -> dict[str, object]:
        self._require(authorization, "api_keys.write")
        return {
            "data": self._service.revoke_api_key(
                api_key_id, request.timestamp
            ).to_dict(),
            "error": None,
        }

    def audit(self, authorization: str | None = None) -> dict[str, object]:
        self._require(authorization, "audit.read")
        return _list(self._service.storage.audit())


def _list(values: tuple[Any, ...]) -> dict[str, object]:
    return {
        "data": [value.to_dict() for value in values],
        "total": len(values),
        "error": None,
    }


def register_routes(app: Any, service: Any, authentication: Any) -> None:
    bridge = EnterpriseApiBridge(service, authentication)
    routes = (
        ("/users", bridge.list_users, ["GET"]),
        ("/users", bridge.create_user, ["POST"]),
        ("/users/{user_id}", bridge.get_user, ["GET"]),
        ("/users/{user_id}", bridge.update_user, ["PATCH"]),
        ("/users/{user_id}/suspend", bridge.suspend, ["POST"]),
        ("/users/{user_id}/restore", bridge.restore, ["POST"]),
        ("/organizations", bridge.list_organizations, ["GET"]),
        ("/organizations", bridge.create_organization, ["POST"]),
        ("/organizations/{organization_id}", bridge.get_organization, ["GET"]),
        ("/organizations/{organization_id}", bridge.update_organization, ["PATCH"]),
        ("/teams", bridge.list_teams, ["GET"]),
        ("/teams", bridge.create_team, ["POST"]),
        ("/teams/{team_id}", bridge.get_team, ["GET"]),
        ("/teams/{team_id}", bridge.update_team, ["PATCH"]),
        ("/teams/{team_id}/members", bridge.add_member, ["POST"]),
        ("/teams/{team_id}/members/{user_id}", bridge.remove_member, ["DELETE"]),
        ("/roles", bridge.list_roles, ["GET"]),
        ("/roles", bridge.create_role, ["POST"]),
        ("/roles/{role_id}/assignments", bridge.assign_role, ["POST"]),
        ("/roles/{role_id}/assignments/{user_id}", bridge.remove_role, ["DELETE"]),
        ("/api-keys", bridge.list_keys, ["GET"]),
        ("/api-keys", bridge.create_key, ["POST"]),
        ("/api-keys/{api_key_id}/revoke", bridge.revoke_key, ["POST"]),
        ("/audit", bridge.audit, ["GET"]),
    )
    for path, endpoint, methods in routes:
        app.add_api_route(path, endpoint, methods=methods, tags=["enterprise"])
