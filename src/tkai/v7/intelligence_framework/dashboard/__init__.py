"""Dashboard projections for the advisory intelligence framework."""
from ..contracts import Scope
from ..framework import GLOBAL_INTELLIGENCE_FRAMEWORK, IntelligenceFramework


class IntelligenceDashboard:
    def __init__(self, framework: IntelligenceFramework | None = None) -> None:
        self.framework = framework or GLOBAL_INTELLIGENCE_FRAMEWORK

    def snapshot(self, scope: Scope) -> dict[str, object]:
        return {
            name: self.framework.projection(name, scope)
            for name in self.framework.PROJECTIONS
        }


__all__ = ("IntelligenceDashboard",)
