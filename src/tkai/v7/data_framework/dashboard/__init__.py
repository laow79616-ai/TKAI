"""Read-only dashboard projections for data metadata."""

from ..contracts import Scope
from ..framework import UnifiedDataFramework

DASHBOARD_SECTIONS = (
    "overview",
    "models",
    "records",
    "schemas",
    "registry",
    "catalog",
    "repositories",
    "adapters",
    "storage",
    "queries",
    "filters",
    "sorting",
    "pagination",
    "indexing",
    "transactions",
    "snapshots",
    "versions",
    "retention",
    "archival",
    "integrity",
    "validation",
    "migration",
    "compatibility",
    "health",
    "metrics",
    "audit",
    "lifecycle",
)


class DataDashboard:
    sections = DASHBOARD_SECTIONS

    def __init__(self, framework: UnifiedDataFramework) -> None:
        self.framework = framework

    def snapshot(self, scope: Scope) -> dict[str, object]:
        return {
            section: self.framework.health(scope)
            if section == "overview"
            else self.framework.projection(section, scope)
            for section in self.sections
        }


__all__ = ("DASHBOARD_SECTIONS", "DataDashboard")
