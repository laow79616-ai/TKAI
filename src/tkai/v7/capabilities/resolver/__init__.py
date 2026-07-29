"""Capability resolution by identity and semantic version."""

from __future__ import annotations

from tkai.v7.capabilities.contracts import CapabilityModel
from tkai.v7.capabilities.framework import CapabilityRegistry
from tkai.v7.contracts import VersionRange


class CapabilityResolver:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    def resolve(
        self, capability_id: str, versions: VersionRange | None = None
    ) -> CapabilityModel:
        return self.registry.lookup(capability_id, versions)


__all__ = ("CapabilityResolver",)
