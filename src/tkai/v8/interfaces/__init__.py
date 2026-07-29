"""Protocols for execution-independent Hyper Kernel integrations."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from tkai.v8.contracts import RegistryRecord, Scope


class MetadataDiscovery(Protocol):
    """Minimal contract implemented by metadata discovery providers."""

    def discover(
        self,
        *,
        scope: Scope | None = None,
        kind: str | None = None,
        capability: str | None = None,
    ) -> tuple[RegistryRecord, ...]: ...


class HealthSource(Protocol):
    """A source that publishes health metadata without being actively probed."""

    def health(self) -> Mapping[str, object]: ...


__all__ = ("HealthSource", "MetadataDiscovery")
