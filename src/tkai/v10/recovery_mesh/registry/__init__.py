"""Bounded, scope-isolated recovery metadata registries."""

from tkai.v10.registries import BoundedRegistry, RegistryError

REGISTRY_NAMES = tuple(
    """profiles contexts strategies plans dependencies readiness validation compatibility
governance integrity trust operations planning decision reasoning knowledge diagnostics
health metrics audit security events contracts interfaces lifecycle""".split()  # noqa: E501
)


class RecoveryRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        for name in (
            "recovery_profile_id",
            "context_id",
            "strategy_id",
            "recovery_plan_id",
            "dependency_id",
            "readiness_id",
            "validation_id",
            "reference_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class RecoveryMeshRegistry:
    NAMES = REGISTRY_NAMES

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: RecoveryRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown recovery mesh registry: {name}") from error


__all__ = ("REGISTRY_NAMES", "RecoveryMeshRegistry", "RecoveryRegistry")
