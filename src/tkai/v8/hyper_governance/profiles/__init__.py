"""Governance profile services."""

from tkai.v8.hyper_governance.contracts import GovernanceProfile
from tkai.v8.hyper_governance.registry import MetadataRegistry

ProfileRegistry = MetadataRegistry[GovernanceProfile]

__all__ = ("GovernanceProfile", "ProfileRegistry")
