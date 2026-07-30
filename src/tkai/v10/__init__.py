"""TKAI V10 local-first sovereign metadata architecture."""

from tkai.v10.contracts import (
    Attestation,
    Boundary,
    ChangePlan,
    Context,
    IntegrityRecord,
    Lifecycle,
    Principal,
    PrincipalType,
    Reference,
    Scope,
    SovereignCoreModel,
    TopologyEdge,
    TrustDomain,
)
from tkai.v10.governance_mesh import SovereignGovernanceMesh
from tkai.v10.integrity_mesh import SovereignIntegrityMesh
from tkai.v10.reasoning_mesh import SovereignReasoningMesh
from tkai.v10.sovereign_core import SovereignCore
from tkai.v10.trust_mesh import SovereignTrustMesh

__all__ = (
    "Attestation",
    "Boundary",
    "ChangePlan",
    "Context",
    "IntegrityRecord",
    "Lifecycle",
    "Principal",
    "PrincipalType",
    "Reference",
    "Scope",
    "SovereignCore",
    "SovereignCoreModel",
    "SovereignIntegrityMesh",
    "SovereignReasoningMesh",
    "SovereignGovernanceMesh",
    "SovereignTrustMesh",
    "TopologyEdge",
    "TrustDomain",
)
