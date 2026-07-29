"""Intelligence metadata lifecycle."""

from tkai.v8.hyper_intelligence.contracts import IntelligenceLifecycle


def authorizes_execution(_value: IntelligenceLifecycle) -> bool:
    return False


__all__ = ("IntelligenceLifecycle", "authorizes_execution")
