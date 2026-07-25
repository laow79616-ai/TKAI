"""Thread-safe reference workflow repository with deterministic filtering."""

from __future__ import annotations

from threading import RLock

from studio.backend.errors import StudioConflictError, StudioNotFoundError
from studio.shared import StudioWorkflow


class InMemoryWorkflowRepository:
    """Store visual workflow snapshots locally; it never executes or compiles them."""

    def __init__(self) -> None:
        self._items: dict[str, StudioWorkflow] = {}
        self._lock = RLock()

    def create(self, workflow: StudioWorkflow) -> StudioWorkflow:
        """Create a workflow and reject an existing workflow identifier."""
        with self._lock:
            if workflow.workflow_id in self._items:
                raise StudioConflictError(
                    f"Workflow already exists: {workflow.workflow_id}"
                )
            self._items[workflow.workflow_id] = workflow
            return workflow

    def get(self, workflow_id: str) -> StudioWorkflow:
        """Return one workflow or raise a stable not-found error."""
        with self._lock:
            try:
                return self._items[workflow_id]
            except KeyError as error:
                raise StudioNotFoundError(
                    f"Workflow not found: {workflow_id}"
                ) from error

    def list(self, *, project_id: str | None = None) -> tuple[StudioWorkflow, ...]:
        """List workflows in stable order, optionally for a single project."""
        with self._lock:
            values = tuple(self._items.values())
            if project_id is not None:
                values = tuple(item for item in values if item.project_id == project_id)
            return tuple(sorted(values, key=lambda item: item.workflow_id))

    def update(self, workflow: StudioWorkflow) -> StudioWorkflow:
        """Replace one immutable workflow snapshot."""
        with self._lock:
            if workflow.workflow_id not in self._items:
                raise StudioNotFoundError(f"Workflow not found: {workflow.workflow_id}")
            self._items[workflow.workflow_id] = workflow
            return workflow

    def delete(self, workflow_id: str) -> None:
        """Delete a local workflow declaration."""
        with self._lock:
            if workflow_id not in self._items:
                raise StudioNotFoundError(f"Workflow not found: {workflow_id}")
            del self._items[workflow_id]

    def ready(self) -> bool:
        """Report local repository readiness without accessing an external store."""
        return True
