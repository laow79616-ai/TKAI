"""Bounded, scope-aware registries for trust metadata."""

from __future__ import annotations

from tkai.v10.registries import BoundedRegistry, RegistryError


class TrustMeshRegistry:
    """Collection of bounded metadata stores."""

    NAMES = (
        "profiles",
        "domains",
        "identities",
        "principals",
        "relationships",
        "integrity",
        "attestations",
        "scores",
        "policies",
        "constraints",
        "governance",
        "compatibility",
        "analytics",
        "diagnostics",
        "health",
        "audit",
        "events",
    )

    def __init__(self, *, per_registry_limit: int = 1_000) -> None:
        self._registries = {
            name: BoundedRegistry(name, limit=per_registry_limit) for name in self.NAMES
        }

    def get(self, name: str) -> BoundedRegistry:
        try:
            return self._registries[name]
        except KeyError as error:
            raise RegistryError(f"unknown trust mesh registry: {name}") from error


__all__ = ("TrustMeshRegistry",)
