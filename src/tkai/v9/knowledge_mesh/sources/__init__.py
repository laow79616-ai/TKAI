"""V6, V7, and V8 source descriptor metadata."""

from tkai.v9.knowledge_mesh.contracts import KnowledgeReference

SourceReference = KnowledgeReference
SUPPORTED_SOURCES = (
    "v6_ai_centers",
    "v7_frameworks",
    "v8_frameworks",
    "v9_components",
)

__all__ = ("SUPPORTED_SOURCES", "SourceReference")
