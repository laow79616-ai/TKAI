"""Read-only dashboard projection for the V7 state framework."""

from __future__ import annotations

from ..framework import GLOBAL_STATE_FRAMEWORK, StateFramework


class StateDashboard:
    sections = (
        "overview",
        "registry",
        "lifecycle",
        "transitions",
        "snapshots",
        "history",
        "consistency",
        "recovery",
        "health",
        "metrics",
        "audit",
    )

    def __init__(self, framework: StateFramework | None = None) -> None:
        self.framework = framework or GLOBAL_STATE_FRAMEWORK

    def snapshot(self) -> dict[str, object]:
        value = self.framework.snapshot()
        return {
            "overview": value["health"],
            **{section: value[section] for section in self.sections[1:]},
        }


__all__ = ("StateDashboard",)
