"""Coordination lifecycle exports."""

from tkai.v8.hyper_coordination.contracts import CoordinationLifecycle

LIFECYCLE_ORDER = tuple(CoordinationLifecycle)


def authorizes_execution(lifecycle: CoordinationLifecycle) -> bool:
    """No lifecycle state, including approved reference, authorizes execution."""

    return False


__all__ = ("CoordinationLifecycle", "LIFECYCLE_ORDER", "authorizes_execution")
