"""In-memory declarative tenant lifecycle for reference tests only."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from threading import RLock

from .errors import TenantLifecycleError
from .tenant import Tenant, TenantStatus


class TenantLifecycleState(str, Enum):
    """Available declarative lifecycle actions."""

    PROVISION = "provision"
    ACTIVATE = "activate"
    SUSPEND = "suspend"
    RESUME = "resume"
    DISABLE = "disable"
    ARCHIVE = "archive"


@dataclass(frozen=True, slots=True)
class TenantLifecycleEvent:
    """Records a local reference transition with a UTC timestamp."""

    tenant_id: str
    action: TenantLifecycleState
    previous_status: TenantStatus
    current_status: TenantStatus
    occurred_at: datetime


class ReferenceTenantLifecycle:
    """Thread-safe state model that never provisions or deletes resources."""

    _TRANSITIONS: dict[tuple[TenantStatus, TenantLifecycleState], TenantStatus] = {
        (TenantStatus.PROVISIONED, TenantLifecycleState.ACTIVATE): TenantStatus.ACTIVE,
        (TenantStatus.ACTIVE, TenantLifecycleState.SUSPEND): TenantStatus.SUSPENDED,
        (TenantStatus.SUSPENDED, TenantLifecycleState.RESUME): TenantStatus.ACTIVE,
        (TenantStatus.ACTIVE, TenantLifecycleState.DISABLE): TenantStatus.DISABLED,
        (TenantStatus.SUSPENDED, TenantLifecycleState.DISABLE): TenantStatus.DISABLED,
        (TenantStatus.DISABLED, TenantLifecycleState.ARCHIVE): TenantStatus.ARCHIVED,
        (TenantStatus.ACTIVE, TenantLifecycleState.ARCHIVE): TenantStatus.ARCHIVED,
    }

    def __init__(self, tenants: tuple[Tenant, ...] = ()) -> None:
        self._tenants = {tenant.tenant_id: tenant for tenant in tenants}
        self._events: list[TenantLifecycleEvent] = []
        self._lock = RLock()

    def provision(self, tenant: Tenant) -> Tenant:
        """Register a local provisioned descriptor without creating any resources."""
        with self._lock:
            if tenant.tenant_id in self._tenants:
                raise TenantLifecycleError(
                    f"Tenant {tenant.tenant_id!r} is already managed."
                )
            provisioned = replace(
                tenant,
                status=TenantStatus.PROVISIONED,
                updated_at=datetime.now(timezone.utc),
            )
            self._tenants[tenant.tenant_id] = provisioned
            self._events.append(
                TenantLifecycleEvent(
                    tenant.tenant_id,
                    TenantLifecycleState.PROVISION,
                    tenant.status,
                    provisioned.status,
                    provisioned.updated_at,
                )
            )
            return provisioned

    def transition(self, tenant_id: str, action: TenantLifecycleState) -> Tenant:
        """Apply a legal local status change or raise a stable lifecycle error."""
        with self._lock:
            try:
                tenant = self._tenants[tenant_id]
                status = self._TRANSITIONS[(tenant.status, action)]
            except KeyError as exc:
                raise TenantLifecycleError(
                    f"Cannot {action.value} tenant {tenant_id!r} in its current state."
                ) from exc
            updated = replace(
                tenant, status=status, updated_at=datetime.now(timezone.utc)
            )
            self._tenants[tenant_id] = updated
            self._events.append(
                TenantLifecycleEvent(
                    tenant_id, action, tenant.status, status, updated.updated_at
                )
            )
            return updated

    def events(self) -> tuple[TenantLifecycleEvent, ...]:
        """Return a stable immutable event snapshot."""
        with self._lock:
            return tuple(self._events)
