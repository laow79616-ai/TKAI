"""Read-only dashboard projection for the V7 Security Framework."""

from ..framework import GLOBAL_SECURITY_FRAMEWORK, SecurityFramework


class SecurityDashboard:
    sections = (
        "overview",
        "policies",
        "roles",
        "permissions",
        "authorization",
        "compliance",
        "secrets",
        "audit",
        "health",
        "metrics",
    )

    def __init__(self, framework: SecurityFramework | None = None) -> None:
        self.framework = framework or GLOBAL_SECURITY_FRAMEWORK

    def snapshot(self) -> dict[str, object]:
        value = self.framework.snapshot()
        return {
            "overview": value["health"],
            **{section: value[section] for section in self.sections[1:]},
        }


__all__ = ("SecurityDashboard",)
