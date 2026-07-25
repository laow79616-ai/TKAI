"""Thread-safe explicit tenant registry with no persistence or worker thread."""

from __future__ import annotations

from threading import RLock

from .errors import TenantConflictError, TenantNotFoundError
from .tenant import Tenant


class TenantRegistry:
    """Stores caller-registered immutable tenants with deterministic snapshots."""

    def __init__(self) -> None:
        self._tenants: dict[str, Tenant] = {}
        self._lock = RLock()

    def register(self, tenant: Tenant) -> None:
        """Register a tenant and reject duplicate identifiers and slugs."""
        with self._lock:
            if tenant.tenant_id in self._tenants or any(
                item.slug == tenant.slug for item in self._tenants.values()
            ):
                raise TenantConflictError(f"Tenant {tenant.tenant_id!r} is duplicate.")
            self._tenants[tenant.tenant_id] = tenant

    def unregister(self, tenant_id: str) -> Tenant:
        """Remove and return a tenant or raise a precise error."""
        with self._lock:
            try:
                return self._tenants.pop(tenant_id)
            except KeyError as exc:
                raise TenantNotFoundError(
                    f"Tenant {tenant_id!r} was not found."
                ) from exc

    def get(self, tenant_id: str) -> Tenant:
        """Return one immutable tenant by id."""
        with self._lock:
            try:
                return self._tenants[tenant_id]
            except KeyError as exc:
                raise TenantNotFoundError(
                    f"Tenant {tenant_id!r} was not found."
                ) from exc

    def lookup_by_slug(self, slug: str) -> Tenant:
        """Return a tenant by slug without storage side effects."""
        with self._lock:
            for tenant in self._tenants.values():
                if tenant.slug == slug:
                    return tenant
        raise TenantNotFoundError(f"Tenant slug {slug!r} was not found.")

    def list(self) -> tuple[Tenant, ...]:
        """Return a stable immutable tenant snapshot."""
        with self._lock:
            return tuple(self._tenants[key] for key in sorted(self._tenants))

    def exists(self, tenant_id: str) -> bool:
        """Return whether an explicit registration exists."""
        with self._lock:
            return tenant_id in self._tenants

    def snapshot(self) -> tuple[Tenant, ...]:
        """Return a safe alias for the stable listing snapshot."""
        return self.list()
