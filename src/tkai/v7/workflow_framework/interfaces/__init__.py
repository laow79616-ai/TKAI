"""Stable workflow framework interfaces."""

from typing import Protocol

from ..contracts import Workflow, WorkflowPlan


class Planner(Protocol):
    def plan(self, workflow_id: str, *, actor: str = "system") -> WorkflowPlan: ...


class Registry(Protocol):
    def register(self, workflow: Workflow) -> Workflow: ...
    def get(self, workflow_id: str) -> Workflow: ...


__all__ = ("Planner", "Registry")
