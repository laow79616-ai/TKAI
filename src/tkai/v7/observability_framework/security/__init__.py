"""Scope isolation and shared V7 secret filtering."""

from tkai.v7.security import filter_secrets

from ..contracts import ObservationScope


def require_scope(
    requested: ObservationScope, tenant: str, workspace: str
) -> ObservationScope:
    if requested.tenant != tenant or requested.workspace != workspace:
        raise PermissionError("observability scope isolation violation")
    return requested


__all__ = ("filter_secrets", "require_scope")
