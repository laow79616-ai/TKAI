"""Hyper Intelligence profile contracts and registry aliases."""

from tkai.v9.knowledge_mesh.contracts import FederationProfile
from tkai.v9.knowledge_mesh.registry import KnowledgeMeshRegistry

ProfileRegistry = KnowledgeMeshRegistry[FederationProfile]

__all__ = ("FederationProfile", "ProfileRegistry")
