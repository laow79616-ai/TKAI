"""Bounded compatibility registries."""

from tkai.v10.registries import BoundedRegistry, RegistryError

REGISTRY_NAMES = tuple(
    """
    profiles versions subjects contracts interfaces schemas capabilities frameworks
    modules services extensions configuration storage runtime apis openapi dashboard
    ai_studio deployment integrity trust governance rules negotiations assessments
    gaps conflicts plans validation diagnostics health metrics audit lifecycle events
    """.split()
)


class CompatibilityRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        if isinstance(record, dict):
            return str(record.get("id") or record.get("version"))
        for name in (
            "profile_id",
            "subject_id",
            "contract_id",
            "interface_id",
            "schema_id",
            "rule_id",
            "negotiation_id",
            "assessment_id",
            "gap_id",
            "conflict_id",
            "plan_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class CompatibilityMeshRegistry:
    NAMES = REGISTRY_NAMES

    def __init__(self, *, per_registry_limit: int = 1000) -> None:
        self._registries = {
            name: CompatibilityRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(
                f"unknown compatibility mesh registry: {name}"
            ) from error
