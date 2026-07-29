"""V7 Unified State Management Framework."""

from .contracts import (
    HealthStatus,
    Lifecycle,
    RecoveryPlan,
    Snapshot,
    StateHealth,
    StateLifecycle,
    StateModel,
    StateRecord,
    StateScope,
    Transition,
    ValidationReport,
)
from .framework import (
    GLOBAL_STATE_FRAMEWORK,
    IllegalTransitionError,
    StateFramework,
    StateRegistry,
    StateSecurity,
    StateValidationError,
    VersionConflictError,
)

__all__ = (
    "GLOBAL_STATE_FRAMEWORK",
    "HealthStatus",
    "IllegalTransitionError",
    "Lifecycle",
    "RecoveryPlan",
    "Snapshot",
    "StateFramework",
    "StateHealth",
    "StateLifecycle",
    "StateModel",
    "StateRecord",
    "StateRegistry",
    "StateScope",
    "StateSecurity",
    "StateValidationError",
    "Transition",
    "ValidationReport",
    "VersionConflictError",
)
