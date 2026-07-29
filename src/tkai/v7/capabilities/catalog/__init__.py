"""Read-only capability catalog."""

from __future__ import annotations

from collections.abc import Iterable

from tkai.v7.capabilities.contracts import CapabilityModel, CapabilityStatus
from tkai.v7.capabilities.framework import CapabilityRegistry


class CapabilityCatalog:
    def __init__(self, registry: CapabilityRegistry) -> None:
        self.registry = registry

    def search(
        self,
        *,
        category: str | None = None,
        owner: str | None = None,
        status: CapabilityStatus | None = None,
        tags: Iterable[str] = (),
    ) -> tuple[CapabilityModel, ...]:
        return self.registry.discover(
            category=category, owner=owner, status=status, tags=tags
        )


__all__ = ("CapabilityCatalog",)
