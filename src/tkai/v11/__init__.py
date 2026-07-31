"""TKAI V11 Autonomous Intelligence Core."""

from tkai.v11.autonomous_core import AutonomousIntelligenceCore
from tkai.v11.contracts import AutonomousCoreModel, IntelligenceProfile, Scope
from tkai.v11.platform import COMPONENTS, V11Platform

__version__ = "11.0.0"

__all__ = (
    "AutonomousCoreModel",
    "AutonomousIntelligenceCore",
    "COMPONENTS",
    "V11Platform",
    "IntelligenceProfile",
    "Scope",
    "__version__",
)
