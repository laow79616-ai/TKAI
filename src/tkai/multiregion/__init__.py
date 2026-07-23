"""Optional local multi-region routing that leaves existing routing unchanged."""

from .doctor import MultiRegionDiagnostic, diagnose
from .errors import MultiRegionError, NoRegionAvailableError, RegionNotFoundError
from .manager import MultiRegionManager
from .models import Region, RegionDecision
from .policy import RegionPolicy
from .policy_adapter import MultiRegionPolicyAdapter
from .regions import RegionRole
from .registry import RegionRegistry
from .router import MultiRegionRouter
from .runtime_adapter import MultiRegionRuntimeAdapter
from .topology import RegionTopology

__all__ = (
    "MultiRegionDiagnostic",
    "MultiRegionError",
    "MultiRegionManager",
    "MultiRegionPolicyAdapter",
    "MultiRegionRouter",
    "MultiRegionRuntimeAdapter",
    "NoRegionAvailableError",
    "Region",
    "RegionDecision",
    "RegionNotFoundError",
    "RegionPolicy",
    "RegionRegistry",
    "RegionRole",
    "RegionTopology",
    "diagnose",
)
