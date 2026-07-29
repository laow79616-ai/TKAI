"""Read-only runtime governance dashboard projection."""

from ..contracts import Scope
from ..framework import GLOBAL_RUNTIME_GOVERNANCE, RuntimeGovernanceFramework

SECTIONS = RuntimeGovernanceFramework.DASHBOARD_SECTIONS


class RuntimeGovernanceDashboard:
    def __init__(self, framework: RuntimeGovernanceFramework | None = None) -> None:
        self.framework = framework or GLOBAL_RUNTIME_GOVERNANCE

    def snapshot(self, scope: Scope) -> dict[str, object]:
        return self.framework.dashboard(scope)


__all__ = ("RuntimeGovernanceDashboard", "SECTIONS")
