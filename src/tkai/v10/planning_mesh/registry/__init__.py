"""Bounded, scope-isolated planning metadata registries."""

from tkai.v10.registries import BoundedRegistry, RegistryError

REGISTRY_NAMES = tuple(
    """profiles contexts objectives milestones dependencies timelines assumptions
constraints risks alternatives plans readiness validation compatibility governance
integrity trust reasoning
decision knowledge diagnostics health metrics audit security events contracts interfaces
lifecycle""".split()
)


class PlanningRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        if isinstance(record, dict):
            value = record.get("id") or record.get("generation")
            if value is not None:
                return str(value)
        for name in (
            "profile_id",
            "context_id",
            "objective_id",
            "milestone_id",
            "dependency_id",
            "timeline_id",
            "readiness_id",
            "validation_id",
            "reference_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class PlanningMeshRegistry:
    NAMES = REGISTRY_NAMES

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: PlanningRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown planning mesh registry: {name}") from error


__all__ = ("PlanningMeshRegistry", "PlanningRegistry", "REGISTRY_NAMES")
