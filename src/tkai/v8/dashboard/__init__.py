"""Transport-neutral Hyper Kernel dashboard snapshot."""

from __future__ import annotations

from tkai.v8.kernel import HyperKernel

DASHBOARD_SECTIONS = (
    "Kernel Overview",
    "Framework Registry",
    "Capabilities",
    "Runtime",
    "Health",
    "Metrics",
    "Diagnostics",
    "Audit",
)


def dashboard_snapshot(kernel: HyperKernel) -> dict[str, object]:
    """Build the complete read-only V8 dashboard model."""

    return {
        "sections": DASHBOARD_SECTIONS,
        "overview": kernel.overview(),
        "frameworks": [
            kernel.serialize_record(record)
            for record in kernel.framework_registry.discover()
        ],
        "capabilities": [
            kernel.serialize_record(record)
            for record in kernel.capability_registry.discover()
        ],
        "runtime": [
            kernel.serialize_record(record)
            for record in kernel.runtime_registry.discover()
        ],
        "health": kernel.health(),
        "metrics": kernel.metrics(),
        "diagnostics": [
            kernel.serialize_diagnostic(item) for item in kernel.diagnostics()
        ],
        "audit": kernel.audit(),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
