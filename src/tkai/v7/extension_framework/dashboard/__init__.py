"""Read-only dashboard projection for the V7 extension framework."""

from __future__ import annotations

from ..contracts import Scope
from ..framework import ExtensionFramework

DASHBOARD_SECTIONS = (
    "catalog",
    "plugins",
    "registry",
    "dependencies",
    "compatibility",
    "validation",
    "packages",
    "signatures",
    "health",
    "metrics",
    "audit",
)


class ExtensionDashboard:
    sections = DASHBOARD_SECTIONS

    def __init__(self, framework: ExtensionFramework) -> None:
        self.framework = framework

    def snapshot(self, scope: Scope) -> dict[str, object]:
        return {
            section: self.framework.projection(section, scope)
            for section in self.sections
        }


__all__ = ("DASHBOARD_SECTIONS", "ExtensionDashboard")
