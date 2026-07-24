"""Tenant component descriptor without external configuration or secret values."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .tenant import TenantValue, snapshot


@dataclass(frozen=True, slots=True)
class TenantDescriptor:
    """Declares optional capabilities without creating a tenant or resources."""

    tenant_id: str
    capabilities: frozenset[str] = field(default_factory=frozenset)
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tenant_id:
            raise ValueError("Tenant descriptor requires a tenant id.")
        object.__setattr__(self, "capabilities", frozenset(self.capabilities))
        object.__setattr__(self, "metadata", snapshot(self.metadata))
