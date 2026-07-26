"""Tenant-isolated workflow execution history."""

from workflow_platform.models import Execution, Scope


class History:
    def __init__(self) -> None:
        self._items: dict[str, Execution] = {}

    def save(self, execution: Execution) -> Execution:
        self._items[execution.id] = execution
        return execution

    def get(self, execution_id: str, scope: Scope) -> Execution:
        item = self._items[execution_id]
        if item.scope != scope:
            raise PermissionError("Tenant or workspace isolation violation.")
        return item

    def list(self, scope: Scope) -> tuple[Execution, ...]:
        return tuple(item for item in self._items.values() if item.scope == scope)
