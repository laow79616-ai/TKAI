"""Read-only dashboard model for resource management metadata."""

from ..framework import GLOBAL_RESOURCE_FRAMEWORK, ResourceFramework


class ResourceDashboard:
    sections = (
        "overview",
        "catalog",
        "registry",
        "capacity",
        "reservations",
        "dependencies",
        "recovery",
        "metrics",
        "health",
        "audit",
    )

    def __init__(self, framework: ResourceFramework | None = None) -> None:
        self.framework = framework or GLOBAL_RESOURCE_FRAMEWORK

    def snapshot(self) -> dict[str, object]:
        value = self.framework.snapshot()
        return {
            "overview": value["health"],
            **{section: value[section] for section in self.sections[1:]},
        }


__all__ = ("ResourceDashboard",)
