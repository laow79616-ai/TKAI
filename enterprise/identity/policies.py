"""Identity policy contracts; no RBAC enforcement is performed here."""

from __future__ import annotations

from typing import Protocol

from .models import IdentityPrincipal, RoleMapping


class IdentityPolicy(Protocol):
    """Maps explicit identity information to role descriptors when invoked."""

    def map_roles(
        self, principal: IdentityPrincipal, mappings: tuple[RoleMapping, ...]
    ) -> frozenset[str]:
        """Return mapped roles without intercepting any Platform request."""
