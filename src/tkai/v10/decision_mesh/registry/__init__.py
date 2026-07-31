"""Bounded, scope-isolated decision metadata registries."""

from tkai.v10.registries import BoundedRegistry, RegistryError

REGISTRY_NAMES = tuple(
    """profiles contexts options criteria evaluations tradeoffs risks dependencies
recommendations confidence limitations governance compatibility integrity trust
reasoning knowledge validation diagnostics health metrics audit security events
contracts interfaces lifecycle""".split()
)


class DecisionRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        if isinstance(record, dict):
            value = record.get("id") or record.get("generation")
            if value is not None:
                return str(value)
        for name in (
            "profile_id",
            "context_id",
            "option_id",
            "criterion_id",
            "evaluation_id",
            "tradeoff_id",
            "risk_id",
            "dependency_id",
            "recommendation_id",
            "confidence_id",
            "limitation_id",
            "reference_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class DecisionMeshRegistry:
    NAMES = REGISTRY_NAMES

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: DecisionRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown decision mesh registry: {name}") from error


__all__ = ("DecisionMeshRegistry", "DecisionRegistry", "REGISTRY_NAMES")
