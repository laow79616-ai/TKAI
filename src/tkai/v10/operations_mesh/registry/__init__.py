"""Bounded, scope-isolated operations metadata registries."""
# ruff: noqa: E501

from tkai.v10.registries import BoundedRegistry, RegistryError

REGISTRY_NAMES = tuple(
    """profiles contexts operations readiness maintenance capacity availability
dependencies assessments governance compatibility integrity trust planning decision
reasoning knowledge validation diagnostics health metrics audit security events contracts
interfaces lifecycle""".split()
)


class OperationsRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        for name in (
            "operations_profile_id",
            "context_id",
            "operation_id",
            "readiness_id",
            "maintenance_id",
            "capacity_id",
            "availability_id",
            "assessment_id",
            "validation_id",
            "reference_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class OperationsMeshRegistry:
    NAMES = REGISTRY_NAMES

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: OperationsRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown operations mesh registry: {name}") from error


__all__ = ("OperationsMeshRegistry", "OperationsRegistry", "REGISTRY_NAMES")
