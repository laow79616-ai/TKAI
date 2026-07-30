"""Bounded, scope-isolated knowledge metadata registries."""

from tkai.v10.registries import BoundedRegistry, RegistryError

REGISTRY_NAMES = tuple(
    """profiles domains concepts entities relationships references evidence provenance
    lineage versions taxonomy ontology classification catalog indexes compatibility
    governance integrity trust validation diagnostics health metrics audit events
    lifecycle""".split()
)


class KnowledgeRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        if isinstance(record, dict):
            value = record.get("id") or record.get("version")
            if value is not None:
                return str(value)
        for name in (
            "profile_id",
            "domain_id",
            "concept_id",
            "entity_id",
            "relationship_id",
            "evidence_id",
            "provenance_id",
            "lineage_id",
            "compatibility_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class KnowledgeMeshRegistry:
    NAMES = REGISTRY_NAMES

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: KnowledgeRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown knowledge mesh registry: {name}") from error


__all__ = ("KnowledgeMeshRegistry", "KnowledgeRegistry", "REGISTRY_NAMES")
