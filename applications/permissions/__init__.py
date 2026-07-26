"""Application permission grants."""

from collections import defaultdict


class PermissionService:
    VALID = frozenset({"view", "edit", "publish", "deploy", "run", "admin"})

    def __init__(self) -> None:
        self._grants: dict[str, dict[str, set[str]]] = defaultdict(dict)

    def grant(
        self, application_id: str, principal: str, permissions: list[str]
    ) -> tuple[str, ...]:
        selected = set(permissions)
        invalid = selected - self.VALID
        if invalid:
            raise ValueError(f"Invalid permissions: {', '.join(sorted(invalid))}")
        self._grants[application_id][principal] = selected
        return tuple(sorted(selected))

    def check(self, application_id: str, principal: str, permission: str) -> bool:
        granted = self._grants[application_id].get(principal, set())
        return permission in granted or "admin" in granted

    def list(self, application_id: str) -> dict[str, tuple[str, ...]]:
        return {
            key: tuple(sorted(value))
            for key, value in self._grants[application_id].items()
        }
