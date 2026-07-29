"""Read-only dashboard projection for V7 configuration."""

from __future__ import annotations

from ..api import CONFIGURATION_ENDPOINTS
from ..contracts import Scope
from ..framework import ConfigurationFramework


class ConfigurationDashboard:
    sections = CONFIGURATION_ENDPOINTS

    def __init__(self, framework: ConfigurationFramework) -> None:
        self.framework = framework

    def snapshot(self, scope: Scope) -> dict[str, object]:
        return {
            section: self.framework.projection(section, scope)
            for section in self.sections
        }


__all__ = ("ConfigurationDashboard",)
