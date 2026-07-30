"""Intelligence metadata lifecycle."""

from tkai.v9.knowledge_mesh.contracts import KnowledgeLifecycle


def authorizes_execution(_value: KnowledgeLifecycle) -> bool:
    return False


__all__ = ("KnowledgeLifecycle", "authorizes_execution")
