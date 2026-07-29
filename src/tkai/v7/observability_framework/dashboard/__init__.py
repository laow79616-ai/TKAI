"""Read-only dashboard projection for V7 observability."""

from ..contracts import ObservationScope
from ..framework import GLOBAL_OBSERVABILITY_FRAMEWORK, ObservabilityFramework


class ObservabilityDashboard:
    sections = (
        "overview",
        "metrics",
        "logging",
        "tracing",
        "diagnostics",
        "health",
        "alerts",
        "telemetry",
        "audit_correlation",
    )

    def __init__(self, framework: ObservabilityFramework | None = None) -> None:
        self.framework = framework or GLOBAL_OBSERVABILITY_FRAMEWORK

    def snapshot(self, scope: ObservationScope) -> dict[str, object]:
        value = self.framework.snapshot(scope)
        return {
            "overview": value["health"],
            "metrics": value["metrics"],
            "logging": value["logging"],
            "tracing": value["tracing"],
            "diagnostics": value["diagnostics"],
            "health": value["health"],
            "alerts": value["alerts"],
            "telemetry": value["telemetry"],
            "audit_correlation": value["audit"],
        }


__all__ = ("ObservabilityDashboard",)
