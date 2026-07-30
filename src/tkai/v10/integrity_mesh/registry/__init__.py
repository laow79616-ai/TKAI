"""Bounded registries for integrity metadata."""

from tkai.v10.registries import BoundedRegistry, RegistryError


class IntegrityRegistry(BoundedRegistry):
    @staticmethod
    def _identifier(record: object) -> str:
        for name in (
            "profile_id",
            "subject_id",
            "evidence_id",
            "verification_id",
            "relationship_id",
            "dependency_id",
            "compatibility_id",
            "release_id",
        ):
            value = getattr(record, name, None)
            if isinstance(value, str):
                return value
        return BoundedRegistry._identifier(record)


class IntegrityMeshRegistry:
    NAMES = (
        "profiles",
        "subjects",
        "evidence",
        "verification",
        "relationships",
        "dependencies",
        "compatibility",
        "configuration",
        "storage",
        "artifacts",
        "releases",
        "diagnostics",
        "health",
        "audit",
        "events",
    )

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: IntegrityRegistry(name, limit=per_registry_limit)
            for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown integrity mesh registry: {name}") from error


__all__ = ("IntegrityMeshRegistry",)
