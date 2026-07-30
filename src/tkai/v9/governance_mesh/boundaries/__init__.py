"""Runtime boundary metadata services."""

from tkai.v9.governance_mesh.contracts import BoundaryRecord, GovernanceScope

BOUNDARY_TYPES = (
    "tenant",
    "workspace",
    "capability",
    "framework",
    "module",
    "extension",
    "configuration",
)

__all__ = ("BOUNDARY_TYPES", "BoundaryRecord", "GovernanceScope")
