"""Hyper Intelligence profile contracts and registry aliases."""

from tkai.v9.intelligence_mesh.contracts import FederationProfile
from tkai.v9.intelligence_mesh.registry import IntelligenceRegistry

ProfileRegistry = IntelligenceRegistry[FederationProfile]

__all__ = ("FederationProfile", "ProfileRegistry")
