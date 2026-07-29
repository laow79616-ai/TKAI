"""TKAI V7 Unified Event Fabric public, backward-compatible contract surface."""

from .contracts import *  # noqa: F403 - intentional stable contract facade
from .contracts import __all__ as _contract_exports
from .dashboard import EventFabricDashboard
from .framework import (
    GLOBAL_FABRIC,
    METRIC_NAMES,
    AuditLog,
    DispatchQueue,
    DispatchQueueFull,
    EventFabric,
    EventFabricError,
    EventRegistry,
    EventRouter,
    EventSecurity,
    EventValidationError,
    IdempotencyStore,
    Metrics,
    ReplayRejected,
    TracingHooks,
    structured_event,
)

__all__ = (
    *_contract_exports,
    "AuditLog",
    "DispatchQueue",
    "DispatchQueueFull",
    "EventFabric",
    "EventFabricDashboard",
    "EventFabricError",
    "EventRegistry",
    "EventRouter",
    "EventSecurity",
    "EventValidationError",
    "GLOBAL_FABRIC",
    "IdempotencyStore",
    "METRIC_NAMES",
    "Metrics",
    "ReplayRejected",
    "TracingHooks",
    "structured_event",
)
