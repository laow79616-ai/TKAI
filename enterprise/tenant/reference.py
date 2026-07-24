"""Reference-only aliases for explicitly selected Tenant Boundary components."""

from .factory import TenantFactory as ReferenceTenantFactory
from .registry import TenantRegistry as ReferenceTenantRegistry

__all__ = ("ReferenceTenantFactory", "ReferenceTenantRegistry")
