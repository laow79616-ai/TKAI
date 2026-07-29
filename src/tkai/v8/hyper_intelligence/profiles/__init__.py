"""Hyper Intelligence profile contracts and registry aliases."""

from tkai.v8.hyper_intelligence.contracts import HyperIntelligenceProfile
from tkai.v8.hyper_intelligence.registry import IntelligenceRegistry

ProfileRegistry = IntelligenceRegistry[HyperIntelligenceProfile]

__all__ = ("HyperIntelligenceProfile", "ProfileRegistry")
