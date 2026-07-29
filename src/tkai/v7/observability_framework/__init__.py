"""V7 Unified Observability and Diagnostics Framework public API."""

from .contracts import (
    Alert,
    AuditCorrelation,
    DiagnosticResult,
    HealthRecord,
    HealthStatus,
    LogRecord,
    MetricDefinition,
    MetricSample,
    Observation,
    ObservationLifecycle,
    ObservationScope,
    Severity,
    Span,
)
from .framework import (
    GLOBAL_OBSERVABILITY_FRAMEWORK,
    DuplicateReferenceError,
    IsolationError,
    MetricRegistry,
    ObservabilityError,
    ObservabilityFramework,
)

__all__ = (
    "Alert",
    "AuditCorrelation",
    "DiagnosticResult",
    "DuplicateReferenceError",
    "GLOBAL_OBSERVABILITY_FRAMEWORK",
    "HealthRecord",
    "HealthStatus",
    "IsolationError",
    "LogRecord",
    "MetricDefinition",
    "MetricRegistry",
    "MetricSample",
    "Observation",
    "ObservationLifecycle",
    "ObservationScope",
    "ObservabilityError",
    "ObservabilityFramework",
    "Severity",
    "Span",
)
