"""V6, V7, and V8 source descriptor metadata."""

from tkai.v9.intelligence_mesh.contracts import IntelligenceReference

SourceReference = IntelligenceReference
SUPPORTED_SOURCES = (
    "v6_ai_centers",
    "v7_frameworks",
    "v8_frameworks",
    "v9_components",
)

__all__ = ("SUPPORTED_SOURCES", "SourceReference")
