"""Trust, tenant, workspace, RBAC, and secret-isolation guards."""

from __future__ import annotations

from tkai.v10.contracts import Scope
from tkai.v10.security import authorize_scope, filter_secrets, validate_safe_metadata


def authorize_metadata_read(
    requested: Scope,
    available: Scope,
    *,
    role_references: tuple[str, ...] = (),
) -> None:
    """Authorize a read without granting trust or runtime permissions."""
    authorize_scope(requested, available)
    if not {"reader", "auditor", "trust-metadata-reader"}.intersection(
        role_references
    ):
        raise PermissionError("RBAC metadata read denied")


def authorize_trust_domain(requested_domain: str, available_domain: str) -> None:
    """Prevent records from crossing a trust-domain boundary."""
    if requested_domain != available_domain:
        raise PermissionError("trust isolation")


__all__ = (
    "authorize_metadata_read",
    "authorize_trust_domain",
    "filter_secrets",
    "validate_safe_metadata",
)
