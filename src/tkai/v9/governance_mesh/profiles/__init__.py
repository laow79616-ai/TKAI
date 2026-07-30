"""Governance profile services."""

from tkai.v9.governance_mesh.contracts import GovernanceProfile
from tkai.v9.governance_mesh.registry import MetadataRegistry

ProfileRegistry = MetadataRegistry[GovernanceProfile]

__all__ = ("GovernanceProfile", "ProfileRegistry")

