"""Read-only dashboard projections for V11 intelligence metadata."""

from typing import Protocol


class IntelligenceProjection(Protocol):
    def overview(self) -> dict[str, object]: ...


DASHBOARD_SECTIONS = (
    "intelligence-overview",
    "autonomous-core",
    "contexts",
    "knowledge",
    "reasoning",
    "decisions",
    "planning",
    "operations",
    "recovery",
    "governance",
    "trust",
    "integrity",
    "compatibility",
    "validation",
    "diagnostics",
    "health",
    "metrics",
    "audit",
)


def dashboard_snapshot(core: IntelligenceProjection) -> dict[str, object]:
    return {
        "sections": DASHBOARD_SECTIONS,
        "overview": core.overview(),
        "read_only": True,
        "actions": (),
    }


__all__ = ("DASHBOARD_SECTIONS", "dashboard_snapshot")
