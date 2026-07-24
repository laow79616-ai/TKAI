"""Declarative tenant isolation models; no actual data or network isolation occurs."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum

from .tenant import TenantValue, snapshot


class TenantIsolationMode(str, Enum):
    """Requested isolation descriptions, explicitly not security guarantees."""

    SHARED = "shared"
    LOGICAL = "logical"
    SCHEMA = "schema"
    DATABASE = "database"
    CLUSTER = "cluster"
    EXTERNAL = "external"


@dataclass(frozen=True, slots=True)
class TenantIsolationDescriptor:
    """States requested scopes without creating or enforcing separation."""

    requested_mode: TenantIsolationMode
    data_scope: str | None = None
    compute_scope: str | None = None
    network_scope: str | None = None
    encryption_scope: str | None = None
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class TenantIsolationDecision:
    """Non-enforcing effective-mode description with an explicit reason."""

    requested_mode: TenantIsolationMode
    effective_mode: TenantIsolationMode
    reason: str
    descriptor: TenantIsolationDescriptor
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))
