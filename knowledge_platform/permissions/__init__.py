"""Knowledge sharing grants."""

from knowledge_platform.models import Permission

PRINCIPALS = {"user", "team", "organization", "application", "agent", "workflow"}


class PermissionService:
    def __init__(self) -> None:
        self.grants: dict[tuple[str, str, str], frozenset[Permission]] = {}

    def grant(
        self, resource_id: str, kind: str, principal_id: str, values: list[str]
    ) -> None:
        if kind not in PRINCIPALS:
            raise ValueError("Unsupported sharing principal.")
        self.grants[(resource_id, kind, principal_id)] = frozenset(
            Permission(value) for value in values
        )

    def check(self, resource_id: str, kind: str, principal_id: str, value: str) -> bool:
        return Permission(value) in self.grants.get(
            (resource_id, kind, principal_id), frozenset()
        )
