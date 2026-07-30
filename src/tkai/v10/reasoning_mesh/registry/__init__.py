"""Bounded, scope-isolated reasoning metadata registries."""
# ruff: noqa: E501

from tkai.v10.registries import BoundedRegistry, RegistryError

REGISTRY_NAMES = tuple(
    """profiles contexts claims premises evidence inferences assumptions constraints
alternatives confidence uncertainty contradictions explanations assessments compatibility governance
integrity trust knowledge validation diagnostics health metrics audit events lifecycle""".split()
)


class ReasoningRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        if isinstance(record, dict):
            value = record.get("id") or record.get("generation")
            if value is not None:
                return str(value)
        for name in (
            "profile_id",
            "context_id",
            "claim_id",
            "premise_id",
            "evidence_id",
            "inference_id",
            "assumption_id",
            "constraint_id",
            "alternative_id",
            "confidence_id",
            "contradiction_id",
            "explanation_id",
            "assessment_id",
            "compatibility_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class ReasoningMeshRegistry:
    NAMES = REGISTRY_NAMES

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: ReasoningRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown reasoning mesh registry: {name}") from error


__all__ = ("REGISTRY_NAMES", "ReasoningMeshRegistry", "ReasoningRegistry")
