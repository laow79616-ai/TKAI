"""Thread-safe execution-record repository for local Studio reference runs."""

from __future__ import annotations

from dataclasses import replace
from threading import RLock

from studio.backend.errors import StudioConflictError, StudioNotFoundError
from studio.shared import ExecutionRecord, ExecutionStatus


class InMemoryExecutionRepository:
    """Store immutable execution records without a queue, worker, or database."""

    def __init__(self) -> None:
        self._items: dict[str, ExecutionRecord] = {}
        self._lock = RLock()

    def create(self, execution: ExecutionRecord) -> ExecutionRecord:
        """Create an execution record with a deterministic duplicate check."""
        with self._lock:
            if execution.execution_id in self._items:
                raise StudioConflictError(
                    f"Execution already exists: {execution.execution_id}"
                )
            self._items[execution.execution_id] = execution
            return execution

    def get(self, execution_id: str) -> ExecutionRecord:
        """Return one immutable execution record."""
        with self._lock:
            try:
                return self._items[execution_id]
            except KeyError as error:
                raise StudioNotFoundError(
                    f"Execution not found: {execution_id}"
                ) from error

    def list(
        self,
        *,
        project_id: str | None = None,
        workflow_id: str | None = None,
    ) -> tuple[ExecutionRecord, ...]:
        """List records in stable identifier order with optional local filters."""
        with self._lock:
            items = tuple(self._items.values())
            if project_id is not None:
                items = tuple(item for item in items if item.project_id == project_id)
            if workflow_id is not None:
                items = tuple(item for item in items if item.workflow_id == workflow_id)
            return tuple(sorted(items, key=lambda item: item.execution_id))

    def update_status(
        self,
        execution_id: str,
        status: ExecutionStatus,
        *,
        output: object | None = None,
        error: str | None = None,
    ) -> ExecutionRecord:
        """Replace record status without exposing a mutable stored instance."""
        with self._lock:
            current = self.get(execution_id)
            updated = replace(current, status=status, output=output, error=error)
            self._items[execution_id] = updated
            return updated

    def ready(self) -> bool:
        """Report local repository readiness without external health probing."""
        return True
