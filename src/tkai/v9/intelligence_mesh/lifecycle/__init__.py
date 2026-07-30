"""Intelligence metadata lifecycle."""

from tkai.v9.intelligence_mesh.contracts import IntelligenceLifecycle


def authorizes_execution(_value: IntelligenceLifecycle) -> bool:
    return False


__all__ = ("IntelligenceLifecycle", "authorizes_execution")
