"""Opt-in TKAI V7 foundation.

Importing this package has no effect on the V6 runtime.
"""

from tkai.v7.contracts import Capability, ModuleDescriptor, Version, VersionRange
from tkai.v7.kernel import Kernel

__version__ = "7.0.0"

__all__ = (
    "Capability",
    "Kernel",
    "ModuleDescriptor",
    "Version",
    "VersionRange",
    "__version__",
)
