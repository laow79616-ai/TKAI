"""Bounded registries for governance metadata."""

from tkai.v10.registries import BoundedRegistry, RegistryError


class GovernanceRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        for name in (
            "profile_id",
            "domain_id",
            "policy_id",
            "constraint_id",
            "review_id",
            "approval_id",
            "risk_id",
            "compliance_id",
            "relationship_id",
            "compatibility_id",
            "validation_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class GovernanceMeshRegistry:
    NAMES = (
        "profiles",
        "domains",
        "policies",
        "constraints",
        "reviews",
        "approvals",
        "risks",
        "compliance",
        "governance",
        "relationships",
        "compatibility",
        "planning",
        "validation",
        "diagnostics",
        "health",
        "metrics",
        "audit",
        "events",
    )

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: GovernanceRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown governance mesh registry: {name}") from error


__all__ = ("GovernanceMeshRegistry",)
