"""Pure tenant routing descriptors and deterministic reference mapping policy."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Protocol

from .context import TenantContext, require_tenant
from .errors import TenantRoutingError
from .tenant import TenantValue, snapshot


@dataclass(frozen=True, slots=True)
class TenantRoute:
    """Describes a route without connecting to a routing system."""

    region: str | None = None
    shard: str | None = None
    cluster: str | None = None
    namespace: str | None = None
    backend: str | None = None
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class TenantRoutingRequest:
    """Explicit request that does not integrate with the Runtime Scheduler."""

    context: TenantContext
    preferred_region: str | None = None
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))


@dataclass(frozen=True, slots=True)
class TenantRoutingDecision:
    """Pure route result that does not migrate data or trigger failover."""

    route: TenantRoute | None
    reason: str
    metadata: Mapping[str, TenantValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", snapshot(self.metadata))


class TenantRoutingPolicy(Protocol):
    """Explicit policy boundary for producing a pure routing descriptor."""

    def route(self, request: TenantRoutingRequest) -> TenantRoutingDecision: ...


class ReferenceTenantRoutingPolicy:
    """Reference-only policy that resolves fixed injected routes."""

    def __init__(self, routes: Mapping[str, TenantRoute]) -> None:
        self._routes = dict(routes)

    def route(self, request: TenantRoutingRequest) -> TenantRoutingDecision:
        """Return a declared route or a stable reference error."""
        tenant_id = require_tenant(request.context).tenant_id
        assert tenant_id is not None
        try:
            return TenantRoutingDecision(self._routes[tenant_id], "reference mapping")
        except KeyError as exc:
            raise TenantRoutingError(
                f"No reference route is declared for tenant {tenant_id!r}."
            ) from exc
