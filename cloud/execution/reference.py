from .factory import ExecutionFactory
from .lifecycle import ExecutionLifecycle
from .registry import ExecutionRegistry


class ReferenceExecutionService:
    def __init__(self, registry=None, factory=None):
        self.registry = registry or ExecutionRegistry()
        self.factory = factory or ExecutionFactory()
        self._lifecycle = ExecutionLifecycle()
        self._closed = False

    def create(self, execution_id, deployment_id, project_id, workspace_id):
        return self.registry.register(
            self.factory.create(execution_id, deployment_id, project_id, workspace_id)
        )

    def get(self, key):
        return self.registry.get(key)

    def list(self):
        return self.registry.list()

    def transition(self, key, target):
        item = self.get(key)
        status = self._lifecycle.transition(item.status, target)
        return type(item)(
            item.execution_id,
            item.deployment_id,
            item.project_id,
            item.workspace_id,
            status,
            item.outcome,
            item.started_at,
            item.finished_at,
            item.metadata,
        )

    def snapshot(self):
        return self.registry.snapshot()

    def close(self):
        self.registry.clear()
        self._closed = True
