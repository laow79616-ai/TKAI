"""Read-only dashboard projection for AI metadata."""

from ..contracts import Scope
from ..framework import UnifiedAIFramework

DASHBOARD_SECTIONS = (
    "overview",
    "providers",
    "models",
    "templates",
    "sessions",
    "evaluation",
    "governance",
    "safety",
    "metrics",
    "audit",
)


class AIDashboard:
    sections = DASHBOARD_SECTIONS

    def __init__(self, framework: UnifiedAIFramework) -> None:
        self.framework = framework

    def snapshot(self, scope: Scope) -> dict[str, object]:
        return {
            section: self.framework.health(scope)
            if section == "overview"
            else self.framework.projection(section, scope)
            for section in self.sections
        }


__all__ = ("AIDashboard", "DASHBOARD_SECTIONS")
