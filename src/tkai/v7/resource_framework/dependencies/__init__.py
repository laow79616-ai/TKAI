"""Resource dependency contracts."""

from ..contracts import DependencyReference
from ..framework import DependencyCycleError

__all__ = ("DependencyCycleError", "DependencyReference")
