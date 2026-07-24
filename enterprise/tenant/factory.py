"""Explicit Tenant factory with caller-provided deterministic identifiers."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from .tenant import Tenant, TenantValue


class TenantFactory:
    """Creates explicitly requested descriptors without global configuration."""

    @staticmethod
    def create(
        *,
        tenant_id: str | None,
        name: str,
        slug: str,
        organization_id: str,
        id_factory: Callable[[], str] | None = None,
        metadata: Mapping[str, TenantValue] | None = None,
    ) -> Tenant:
        """Use a supplied id or an injected id factory; never generate a hidden id."""
        resolved_id = tenant_id or (id_factory() if id_factory else None)
        if not resolved_id:
            raise ValueError("TenantFactory requires an id or injected id factory.")
        return Tenant(resolved_id, name, slug, organization_id, metadata=metadata or {})
