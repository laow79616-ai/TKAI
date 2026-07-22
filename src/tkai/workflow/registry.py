"""Workflow definition registry."""

from __future__ import annotations

from tkai.core.exceptions import WorkflowError

from .models import Workflow, WorkflowDefinition


class WorkflowNotFoundError(WorkflowError):
    """Unknown workflow."""


class WorkflowValidationError(WorkflowError):
    """Invalid workflow."""


class WorkflowRegistry:
    def __init__(self) -> None:
        self._items: dict[str, WorkflowDefinition] = {}

    def register(self, definition: WorkflowDefinition) -> None:
        if definition.name in self._items:
            raise WorkflowError(f"Workflow '{definition.name}' already registered")
        self._items[definition.name] = definition

    def unregister(self, name: str) -> WorkflowDefinition:
        try:
            return self._items.pop(name)
        except KeyError as exc:
            raise WorkflowNotFoundError(name) from exc

    def get(self, name: str) -> WorkflowDefinition:
        try:
            return self._items[name]
        except KeyError as exc:
            raise WorkflowNotFoundError(name) from exc

    def list(self) -> list[str]:
        return sorted(self._items)

    def create(self, definition: WorkflowDefinition) -> Workflow:
        self.register(definition)
        return Workflow(definition)
