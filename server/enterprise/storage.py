"""Thread-safe pure-memory Enterprise storage, suitable for explicit replacement."""

from __future__ import annotations

from threading import RLock
from typing import Protocol, cast

from .errors import (
    EnterpriseClosedError,
    EnterpriseConflictError,
    EnterpriseNotFoundError,
)
from .models import (
    ApiKeyRecord,
    AuditEvent,
    EnterpriseSnapshot,
    EnterpriseStatistics,
    OrganizationRecord,
    RoleAssignment,
    RoleRecord,
    TeamRecord,
    UserRecord,
)


class EnterpriseStorage(Protocol):
    def snapshot(self) -> EnterpriseSnapshot: ...
    def statistics(self) -> EnterpriseStatistics: ...
    def close(self) -> None: ...


class ReferenceEnterpriseStorage:
    """Instance-isolated Enterprise storage with deterministic ordering and no I/O."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._users: dict[str, UserRecord] = {}
        self._organizations: dict[str, OrganizationRecord] = {}
        self._teams: dict[str, TeamRecord] = {}
        self._roles: dict[str, RoleRecord] = {}
        self._assignments: set[RoleAssignment] = set()
        self._keys: dict[str, ApiKeyRecord] = {}
        self._audit: list[AuditEvent] = []
        self._credentials: dict[str, str] = {}
        self._closed = False

    def create(self, collection: str, value: object, identifier: str) -> object:
        with self._lock:
            self._open()
            target = self._collection(collection)
            if identifier in target:
                raise EnterpriseConflictError("Enterprise record already exists.")
            target[identifier] = value
            return value

    def update(self, collection: str, value: object, identifier: str) -> object:
        with self._lock:
            self._open()
            target = self._collection(collection)
            if identifier not in target:
                raise EnterpriseNotFoundError("Enterprise record was not found.")
            target[identifier] = value
            return value

    def get(self, collection: str, identifier: str) -> object:
        with self._lock:
            self._open()
            try:
                return self._collection(collection)[identifier]
            except KeyError as error:
                raise EnterpriseNotFoundError(
                    "Enterprise record was not found."
                ) from error

    def list(self, collection: str) -> tuple[object, ...]:
        with self._lock:
            self._open()
            return tuple(
                self._collection(collection)[key]
                for key in sorted(self._collection(collection))
            )

    def add_assignment(self, assignment: RoleAssignment) -> None:
        with self._lock:
            self._open()
            self._assignments.add(assignment)

    def remove_assignment(self, assignment: RoleAssignment) -> None:
        with self._lock:
            self._open()
            self._assignments.discard(assignment)

    def assignments(self) -> tuple[RoleAssignment, ...]:
        with self._lock:
            return tuple(
                sorted(
                    self._assignments,
                    key=lambda item: (str(item.user_id), str(item.role_id)),
                )
            )

    def append_audit(self, event: AuditEvent) -> None:
        with self._lock:
            self._open()
            self._audit.append(event)

    def audit(self) -> tuple[AuditEvent, ...]:
        with self._lock:
            return tuple(self._audit)

    def snapshot(self) -> EnterpriseSnapshot:
        with self._lock:
            users = tuple(self._users[key] for key in sorted(self._users))
            orgs = tuple(
                self._organizations[key] for key in sorted(self._organizations)
            )
            teams = tuple(self._teams[key] for key in sorted(self._teams))
            roles = tuple(self._roles[key] for key in sorted(self._roles))
            keys = tuple(self._keys[key] for key in sorted(self._keys))
            return EnterpriseSnapshot(
                users,
                orgs,
                teams,
                roles,
                keys,
                tuple(self._audit),
                self.statistics(),
                self._closed,
            )

    def statistics(self) -> EnterpriseStatistics:
        return EnterpriseStatistics(
            len(self._users),
            len(self._organizations),
            len(self._teams),
            len(self._roles),
            len(self._keys),
            len(self._audit),
        )

    def close(self) -> None:
        with self._lock:
            self._closed = True

    def _open(self) -> None:
        if self._closed:
            raise EnterpriseClosedError("Enterprise storage is closed.")

    def _collection(self, name: str) -> dict[str, object]:
        collections: dict[str, object] = {
            "users": self._users,
            "organizations": self._organizations,
            "teams": self._teams,
            "roles": self._roles,
            "api_keys": self._keys,
        }
        return cast(dict[str, object], collections[name])
