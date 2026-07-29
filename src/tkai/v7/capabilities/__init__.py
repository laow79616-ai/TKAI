"""TKAI V7 Unified Capability Framework.

The framework is opt-in and does not alter the V6 runtime or TikTok behavior.
"""

from tkai.v7.capabilities.contracts import (
    CapabilityModel,
    CapabilityProvider,
    CapabilityStatus,
    Dependency,
    Deprecation,
    Health,
    HealthStatus,
    Interface,
    Metrics,
    UpgradePath,
    serialize,
)
from tkai.v7.capabilities.dashboard import CapabilityDashboard
from tkai.v7.capabilities.framework import (
    GLOBAL_REGISTRY,
    AuditLog,
    CapabilityError,
    CapabilityLifecycle,
    CapabilityLoader,
    CapabilityMetrics,
    CapabilityNotFoundError,
    CapabilityRegistry,
    CapabilityValidationError,
    CapabilityValidator,
    DependencyCycleError,
    DependencyGraph,
    HealthMonitor,
    LifecycleTransitionError,
    compatible,
)

__all__ = (
    "GLOBAL_REGISTRY",
    "AuditLog",
    "CapabilityDashboard",
    "CapabilityError",
    "CapabilityLifecycle",
    "CapabilityLoader",
    "CapabilityMetrics",
    "CapabilityModel",
    "CapabilityNotFoundError",
    "CapabilityProvider",
    "CapabilityRegistry",
    "CapabilityStatus",
    "CapabilityValidationError",
    "CapabilityValidator",
    "Dependency",
    "DependencyCycleError",
    "DependencyGraph",
    "Deprecation",
    "Health",
    "HealthMonitor",
    "HealthStatus",
    "Interface",
    "LifecycleTransitionError",
    "Metrics",
    "UpgradePath",
    "compatible",
    "serialize",
)
