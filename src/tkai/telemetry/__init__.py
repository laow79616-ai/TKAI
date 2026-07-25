"""Optional provider-neutral telemetry platform with local default exporters."""

from .context import CorrelationContext
from .errors import ExporterNotFoundError, TelemetryError
from .exporter import (
    ConsoleExporter,
    InMemoryExporter,
    LocalExporter,
    OTLPExporter,
    PrometheusExporter,
    TelemetryExporter,
)
from .integrations import TelemetryIntegration
from .logging import TelemetryLoggingAdapter
from .manager import TelemetryManager
from .metrics import MetricsRegistry
from .models import Metric, MetricKind, StructuredLog, TraceContext
from .platform import (
    LogLevel,
    Span,
    SpanStatus,
    TelemetryContext,
    TelemetryPlatform,
    TelemetryProvider,
    Trace,
)
from .policy_adapter import TelemetryPolicyAdapter
from .registry import TelemetryRegistry
from .runtime_adapter import TelemetryRuntimeAdapter
from .sampling import AlwaysOffSampler, AlwaysOnSampler, ProbabilitySampler, Sampler
from .tracing import TraceRegistry

__all__ = (
    "CorrelationContext",
    "ConsoleExporter",
    "ExporterNotFoundError",
    "InMemoryExporter",
    "LocalExporter",
    "LogLevel",
    "Metric",
    "MetricKind",
    "MetricsRegistry",
    "OTLPExporter",
    "AlwaysOffSampler",
    "AlwaysOnSampler",
    "ProbabilitySampler",
    "PrometheusExporter",
    "Sampler",
    "Span",
    "SpanStatus",
    "StructuredLog",
    "TelemetryError",
    "TelemetryExporter",
    "TelemetryLoggingAdapter",
    "TelemetryManager",
    "TelemetryContext",
    "TelemetryIntegration",
    "TelemetryPolicyAdapter",
    "TelemetryPlatform",
    "TelemetryProvider",
    "TelemetryRegistry",
    "TelemetryRuntimeAdapter",
    "TraceContext",
    "Trace",
    "TraceRegistry",
)
