"""Declarative tenant quotas and a reference-only local calculator."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .errors import TenantQuotaError
from .tenant import TenantValue, snapshot


class TenantQuotaResource(str, Enum):
    """Named resources commonly described by tenant quota declarations."""

    REQUESTS = "requests"
    EXECUTIONS = "executions"
    WORKFLOWS = "workflows"
    AGENTS = "agents"
    PROVIDERS = "providers"
    STORAGE = "storage"
    MEMORY_RECORDS = "memory_records"
    USERS = "users"
    TEAMS = "teams"


@dataclass(frozen=True, slots=True)
class TenantQuotaLimit:
    """Non-negative quota limit without billing, limiting, or persistence."""

    resource: str
    limit: int | None

    def __post_init__(self) -> None:
        if not self.resource or self.limit is not None and self.limit < 0:
            raise TenantQuotaError(
                "Quota resource and non-negative limit are required."
            )


@dataclass(frozen=True, slots=True)
class TenantQuotaUsage:
    """Caller-supplied usage observation that is never persisted or incremented."""

    resource: str
    used: int

    def __post_init__(self) -> None:
        if not self.resource or self.used < 0:
            raise TenantQuotaError(
                "Quota resource and non-negative usage are required."
            )


@dataclass(frozen=True, slots=True)
class TenantQuota:
    """Tenant-scoped immutable limits and usage descriptors."""

    tenant_id: str
    limits: tuple[TenantQuotaLimit, ...] = ()
    usage: tuple[TenantQuotaUsage, ...] = ()
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.tenant_id:
            raise TenantQuotaError("Tenant quota requires a tenant id.")
        object.__setattr__(self, "limits", tuple(self.limits))
        object.__setattr__(self, "usage", tuple(self.usage))
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class TenantQuotaDecision:
    """Calculation result that never blocks a Platform request."""

    allowed: bool
    resource: str
    limit: int | None
    used: int
    remaining: int | None
    reason: str
    reset_at: datetime | None = None


class ReferenceTenantQuotaService:
    """Reference-only calculator using injected immutable quota observations."""

    def __init__(self, quotas: Mapping[str, TenantQuota]) -> None:
        self._quotas = dict(quotas)

    def check(self, tenant_id: str, resource: str) -> TenantQuotaDecision:
        """Calculate a descriptor without consuming, billing, or rate limiting."""
        try:
            quota = self._quotas[tenant_id]
        except KeyError as exc:
            raise TenantQuotaError(
                f"No quota exists for tenant {tenant_id!r}."
            ) from exc
        limits = {item.resource: item.limit for item in quota.limits}
        usage = {item.resource: item.used for item in quota.usage}
        limit = limits.get(resource)
        used = usage.get(resource, 0)
        remaining = None if limit is None else max(limit - used, 0)
        return TenantQuotaDecision(
            limit is None or used < limit,
            resource,
            limit,
            used,
            remaining,
            "reference quota computed",
        )
