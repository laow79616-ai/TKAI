"""Resource lifecycle contracts and transitions."""

from ..contracts import ResourceLifecycle
from ..framework import LIFECYCLE_TRANSITIONS, IllegalLifecycleTransition

__all__ = (
    "IllegalLifecycleTransition",
    "LIFECYCLE_TRANSITIONS",
    "ResourceLifecycle",
)
