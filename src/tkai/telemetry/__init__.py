"""Optional local telemetry foundation with no network exporters."""

from .context import CorrelationContext
from .errors import ExporterNotFoundError, TelemetryError
from .exporter import LocalExporter, TelemetryExporter
from .logging import TelemetryLoggingAdapter
from .manager import TelemetryManager
from .metrics import MetricsRegistry
from .models import Metric, MetricKind, StructuredLog, TraceContext
from .policy_adapter import TelemetryPolicyAdapter
from .registry import TelemetryRegistry
from .runtime_adapter import TelemetryRuntimeAdapter
from .tracing import TraceRegistry

__all__ = (
    "CorrelationContext",
    "ExporterNotFoundError",
    "LocalExporter",
    "Metric",
    "MetricKind",
    "MetricsRegistry",
    "StructuredLog",
    "TelemetryError",
    "TelemetryExporter",
    "TelemetryLoggingAdapter",
    "TelemetryManager",
    "TelemetryPolicyAdapter",
    "TelemetryRegistry",
    "TelemetryRuntimeAdapter",
    "TraceContext",
    "TraceRegistry",
)
