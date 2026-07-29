"""Read-only dashboard model for workflow orchestration metadata."""

from ..framework import GLOBAL_WORKFLOW_FRAMEWORK, WorkflowFramework


class WorkflowDashboard:
    sections = (
        "overview",
        "definitions",
        "planner",
        "dependencies",
        "constraints",
        "lifecycle",
        "history",
        "recovery",
        "metrics",
        "audit",
    )

    def __init__(self, framework: WorkflowFramework | None = None) -> None:
        self.framework = framework or GLOBAL_WORKFLOW_FRAMEWORK

    def snapshot(self) -> dict[str, object]:
        value = self.framework.snapshot()
        return {
            "overview": value["health"],
            **{section: value[section] for section in self.sections[1:]},
        }


__all__ = ("WorkflowDashboard",)
