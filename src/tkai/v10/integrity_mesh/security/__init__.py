"""RBAC, scope-isolation, and safe-metadata guards."""

from tkai.v10.contracts import Scope
from tkai.v10.security import authorize_scope, filter_secrets, validate_safe_metadata


def authorize_metadata_read(
    requested: Scope,
    available: Scope,
    *,
    role_references: tuple[str, ...] = (),
) -> None:
    authorize_scope(requested, available)
    if not {"reader", "auditor", "integrity-metadata-reader"}.intersection(
        role_references
    ):
        raise PermissionError("RBAC metadata read denied")


__all__ = (
    "authorize_metadata_read",
    "filter_secrets",
    "validate_safe_metadata",
)
