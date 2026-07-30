"""Bounded lineage metadata."""

from tkai.v9.knowledge_mesh.models import Lineage

MAX_LINEAGE_DEPTH = 32
__all__ = ("Lineage", "MAX_LINEAGE_DEPTH")
